import pyoxigraph
from pyoxigraph import Store, NamedNode
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import openai  
import json
import os
from pathlib import Path

class OgenEngine:
  def __init__(self, openai_api_key: str): 
    
    self.client = openai.OpenAI(api_key=openai_api_key) 

    self.store = Store()

    self.GRAPH_CORE = NamedNode("http://ogen.ai/graph/core")
    self.GRAPH_USER = NamedNode("http://ogen.ai/graph/user")
    self.GRAPH_CONTEXT = NamedNode("http://ogen.ai/graph/context")

    # 온톨로지 파일 경로 (패키지 내부)
    current_dir = Path(__file__).parent
    ontology_path = current_dir / "ogen-core.ttl"

    try:
      with open(ontology_path, "rb") as f:
        # pyoxigraph의 load는 기본적으로 기본 그래프에 로드됨
        # Named Graph을 사용하려면 쿼리 시 FROM 절 사용
        self.store.load(f, "text/turtle", base_iri="http://ogen.ai/ontology/")
      print("✅ Ontology Loaded from package!")
    except FileNotFoundError:
      print(f"❌ Error: {ontology_path} not found")
      raise

    self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
    self.nodes = []
    self.node_embeddings = []
    self.user_data_loaded = False
    
    self._build_index()
  
  def _build_index(self):
    """Embed all nodes in the graph (GRAPH_CORE + GRAPH_USER 통합 검색)"""

    query = """
    PREFIX ex: <http://ogen.ai/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?s ?label ?comment ?keywords WHERE {
      ?s rdfs:label ?label .
      OPTIONAL { ?s rdfs:comment ?comment }
      OPTIONAL { ?s ex:keywords ?keywords }
    }
    """

    # 기존 인덱스 초기화
    self.nodes = []
    
    results = self.store.query(query)

    for binding in results:
      uri = binding["s"].value
      label = binding["label"].value
      search_text = f"{label}"
      if "keywords" in binding:
          search_text += f" {binding['keywords'].value}"
      if "comment" in binding:
            search_text += f" {binding['comment'].value}"
      
      self.nodes.append({
          "uri": uri, 
          "label": label, 
          "search_text": search_text 
      })
       

    if self.nodes:
      labels = [n["label"] for n in self.nodes]
      self.node_embeddings = self.embedder.encode(labels)
      print(f"📊 Index rebuilt: {len(self.nodes)} nodes")

  def get_subgraph_context(self, anchor_uri: str):
    anchor_sparql_ref = f"<{anchor_uri}>" if not anchor_uri.startswith("<") else anchor_uri

    query = f"""
    PREFIX ex: <http://ogen.ai/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?part ?label ?propType ?propSchema ?validationRules ?layoutType ?flexDirection ?spacing ?ariaLabel ?role ?defaultState ?variant WHERE {{
      {anchor_sparql_ref} ex:hasPart ?part .
      ?part rdfs:label ?label .
      OPTIONAL {{ ?part ex:propType ?propType }}
      OPTIONAL {{ ?part ex:propSchema ?propSchema }}
      OPTIONAL {{ ?part ex:validationRules ?validationRules }}
      OPTIONAL {{ ?part ex:layoutType ?layoutType }}
      OPTIONAL {{ ?part ex:flexDirection ?flexDirection }}
      OPTIONAL {{ ?part ex:spacing ?spacing }}
      OPTIONAL {{ ?part ex:ariaLabel ?ariaLabel }}
      OPTIONAL {{ ?part ex:role ?role }}
      OPTIONAL {{ ?part ex:defaultState ?defaultState }}
      OPTIONAL {{ ?part ex:variant ?variant }}
    }}
    """
    
    results = self.store.query(query)
    parts = []
    for binding in results:
      part_uri = binding["part"].value
      part_info = {
        "type": part_uri.split("/")[-1],
        "label": binding["label"].value,
        "propType": binding["propType"].value if "propType" in binding else None
      }
      
      # 추가 속성들 포함
      if "propSchema" in binding:
        try:
          import json
          part_info["propSchema"] = json.loads(binding["propSchema"].value)
        except:
          part_info["propSchema"] = binding["propSchema"].value
      
      if "validationRules" in binding:
        try:
          import json
          part_info["validationRules"] = json.loads(binding["validationRules"].value)
        except:
          part_info["validationRules"] = binding["validationRules"].value
      
      if "layoutType" in binding:
        part_info["layoutType"] = binding["layoutType"].value
      
      if "flexDirection" in binding:
        part_info["flexDirection"] = binding["flexDirection"].value
      
      if "spacing" in binding:
        part_info["spacing"] = binding["spacing"].value
      
      if "ariaLabel" in binding:
        part_info["ariaLabel"] = binding["ariaLabel"].value
      
      if "role" in binding:
        part_info["role"] = binding["role"].value
      
      if "defaultState" in binding:
        part_info["defaultState"] = binding["defaultState"].value
      
      if "variant" in binding:
        part_info["variant"] = binding["variant"].value
      
      parts.append(part_info)
    return parts
  
  def analyze_requirement(self, user_query: str) -> dict:
    """
    [Requirement Analysis Step]
    사용자 요청을 분석하여 필요한 UI 컴포넌트와 기능을 파악
    
    Returns:
        dict: {
            "required_components": [{"type": str, "purpose": str, "keywords": [str]}],
            "user_intent": str,
            "suggested_anchor": str or None,
            "required_features": [str]
        }
    """
    system_prompt = """
    You are a UI requirement analyzer. Your job is to analyze user requests and determine what UI components and features are needed.
    
    Analyze the user's request and extract:
    1. What UI components are needed (e.g., login form, search bar, button)
    2. The user's intent (what they want to accomplish)
    3. Suggested component names that might match the Knowledge Graph
    4. Required features (validation, accessibility, etc.)
    
    IMPORTANT: You must return the result in pure JSON format.
    Output Schema: {
        "required_components": [{"type": "string", "purpose": "string", "keywords": ["string"]}],
        "user_intent": "string",
        "suggested_anchor": "string or null",
        "required_features": ["string"]
    }
    """

    user_prompt = f"""
    User Query: "{user_query}"
    
    Analyze this request and determine:
    1. What UI components are needed to fulfill this request
    2. The user's intent
    3. A suggested component name that might exist in the Knowledge Graph (e.g., "LoginCard", "SearchBar")
    4. Required features (e.g., "email validation", "password strength", "accessibility")
    
    Return the analysis in JSON format.
    """

    response = self.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    analysis = json.loads(response.choices[0].message.content)
    print(f"📋 Requirement Analysis: {json.dumps(analysis, ensure_ascii=False, indent=2)}")
    
    return analysis

  def find_anchor_node_with_llm(self, user_query: str, requirement_analysis: dict = None, top_k: int = 5):
    """
    [Agentic Selection Step]
    1. Vector Search로 후보군(Candidates)을 좁힘 (Pre-filtering)
    2. LLM이 후보군 중에서 사용자의 의도에 가장 적합한 앵커를 선택 (Reasoning)
    
    Args:
        user_query: 사용자 요청
        requirement_analysis: analyze_requirement의 결과 (선택적, 있으면 더 정확한 검색)
        top_k: 검색할 후보 개수
    """
    if not self.nodes:
      return None

    # 요청 분석 결과가 있으면 suggested_anchor를 키워드로 활용
    search_query = user_query
    if requirement_analysis and requirement_analysis.get("suggested_anchor"):
      search_query = f"{user_query} {requirement_analysis['suggested_anchor']}"
      # required_components의 키워드도 추가
      for comp in requirement_analysis.get("required_components", []):
        if comp.get("keywords"):
          search_query += " " + " ".join(comp["keywords"])

    query_vec = self.embedder.encode([search_query])
    similarities = cosine_similarity(query_vec, self.node_embeddings)[0]
    
    top_k_indices = np.argsort(similarities)[::-1][:top_k]
    
    candidates = []
    for idx in top_k_indices:
      node = self.nodes[idx]
      score = similarities[idx]
      candidates.append({
          "uri": node["uri"], 
          "label": node["label"], 
          "score": float(score)
      })

    print(f"🕵️ Candidates found: {[c['label'] for c in candidates]}")

    # 요청 분석 결과를 프롬프트에 포함
    analysis_context = ""
    if requirement_analysis:
      analysis_context = f"""
    [Requirement Analysis]
    User Intent: {requirement_analysis.get('user_intent', 'N/A')}
    Required Components: {json.dumps(requirement_analysis.get('required_components', []), ensure_ascii=False)}
    Suggested Anchor: {requirement_analysis.get('suggested_anchor', 'N/A')}
    """

    system_prompt = """
    You are a semantic router for a UI Knowledge Graph.
    Select the most appropriate 'Target Component' URI from the candidates based on the user's intent.
    If none of the candidates are suitable, return null.
    
    IMPORTANT: You must return the result in pure JSON format.
    Output Schema: {"selected_uri": "string" or null, "reason": "string"}
    """

    user_prompt = f"""
    User Query: "{user_query}"
    {analysis_context}
    Candidates:
    {json.dumps(candidates, ensure_ascii=False, indent=2)}
    
    Select the best anchor node and return JSON.
    """

    response = self.client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    decision = json.loads(response.choices[0].message.content)
    
    selected_uri = decision.get("selected_uri")
    print(f"🎯 LLM Selected: {selected_uri} (Reason: {decision.get('reason')})")

    return selected_uri

  def reason(self, user_query: str, context_mode: str = "default"):
    """
    LLM Reasoning Stage:
    1. Analyze User Requirement (요청 분석)
    2. Find Anchor Node based on Analysis (KG 기반 추론)
    3. Retrieve Graph Context (Facts)
    4. Construct Prompt (Instruction + Facts + Analysis)
    5. Generate Output (LLM Inference)
    """

    # Step 1: 요청 분석
    print(f"🔍 Step 1: Analyzing requirement for query: '{user_query}'")
    requirement_analysis = self.analyze_requirement(user_query)
    
    # Step 2: 요청 분석 결과를 바탕으로 앵커 노드 찾기
    print(f"🔍 Step 2: Finding anchor node based on analysis")
    anchor_uri = self.find_anchor_node_with_llm(user_query, requirement_analysis)
    
    if not anchor_uri:
      # 앵커를 찾지 못했지만, 요청 분석 결과가 있으면 그것을 바탕으로 UI 생성 시도
      if requirement_analysis and requirement_analysis.get("suggested_anchor"):
        suggested = requirement_analysis["suggested_anchor"]
        print(f"⚠️ Anchor not found, but trying with suggested: {suggested}")
        # suggested_anchor를 URI 형식으로 변환 시도
        # 사용자 데이터에서 찾기
        for node in self.nodes:
          if suggested.lower() in node["label"].lower() or node["label"].lower() in suggested.lower():
            anchor_uri = node["uri"]
            print(f"✅ Found matching node: {node['label']} -> {anchor_uri}")
            break
        
        if not anchor_uri:
          # 여전히 찾지 못하면 요청 분석 결과만으로 UI 생성
          return self._generate_ui_from_analysis(user_query, requirement_analysis, context_mode)
      else:
        return {"error": "요청하신 UI 컴포넌트를 지식 그래프에서 찾을 수 없습니다."}
    
    # Step 3: Graph Context 검색
    anchor_name = anchor_uri.split("/")[-1]
    print(f"📚 Step 3: Retrieving graph context for anchor: {anchor_name}")
    retrieved_children = self.get_subgraph_context(anchor_uri)
    
    # Step 4 & 5: UI 생성
    return self._generate_ui_with_context(
        user_query, 
        requirement_analysis, 
        anchor_name, 
        retrieved_children, 
        context_mode
    )

  def _generate_ui_from_analysis(self, user_query: str, requirement_analysis: dict, context_mode: str) -> dict:
    """
    요청 분석 결과만으로 UI 생성 (KG에서 컴포넌트를 찾지 못한 경우)
    """
    constraints = []
    if context_mode == "low-vision":
      constraints = ["High Contrast Theme", "Base Font Size 24px"]

    system_prompt = f"""
    You are an expert UI Compiler. Your job is to generate a JSON specification for a UI component based on the user's request and requirement analysis.
    
    [RULES]
    1. Generate appropriate UI components based on the requirement analysis.
    2. Apply the 'Constraints' to the properties of the components.
    3. Use standard HTML form elements and components (input, button, form, etc.).
    4. Apply validation rules when generating input components.
    5. Use proper layout (flex, column direction, spacing).
    6. Include accessibility attributes (ariaLabel, role).
    7. Set appropriate defaultState, variant, and other style properties.
    8. Output must be valid JSON with the following structure:
       {{
         "type": "component_name",
         "props": {{ ... }},
         "children": [ ... ]
       }}
    """

    user_prompt = f"""
    User Query: "{user_query}"
    
    [Requirement Analysis]
    User Intent: {requirement_analysis.get('user_intent', 'N/A')}
    Required Components: {json.dumps(requirement_analysis.get('required_components', []), ensure_ascii=False, indent=2)}
    Required Features: {json.dumps(requirement_analysis.get('required_features', []), ensure_ascii=False)}
    
    [Constraints]
    - {", ".join(constraints) if constraints else "None"}
    
    Generate the UI JSON spec now. Create a complete and accessible component specification based on the requirement analysis.
    """

    response = self.client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"} 
    )

    llm_output = json.loads(response.choices[0].message.content)

    return {
        "source_anchor": requirement_analysis.get("suggested_anchor", "generated"),
        "reasoning_mode": context_mode,
        "generated_spec": llm_output,
        "requirement_analysis": requirement_analysis
    }

  def _generate_ui_with_context(
      self, 
      user_query: str, 
      requirement_analysis: dict, 
      anchor_name: str, 
      retrieved_children: list, 
      context_mode: str
  ) -> dict:
    """
    Graph Context를 활용하여 UI 생성
    """
    constraints = []
    if context_mode == "low-vision":
      constraints = ["High Contrast Theme", "Base Font Size 24px"]

    system_prompt = f"""
    You are an expert UI Compiler powered by a Knowledge Graph.
    Your job is to generate a JSON specification for a UI component based on the user's request.
    
    [RULES]
    1. STRICTLY use only the child components provided in the 'Graph Context'. Do not hallucinate new components.
    2. Apply the 'Constraints' to the properties of the components.
    3. Use the propSchema information to set appropriate default values and types.
    4. Apply validationRules when generating input components.
    5. Use layoutType, flexDirection, and spacing for proper layout.
    6. Include accessibility attributes (ariaLabel, role) when available.
    7. Set appropriate defaultState, variant, and other style properties.
    8. Consider the requirement analysis to ensure the generated UI matches user intent.
    9. Output must be valid JSON with the following structure:
       {{
         "type": "component_name",
         "props": {{ ... }},
         "children": [ ... ]
       }}
    """

    analysis_summary = ""
    if requirement_analysis:
      analysis_summary = f"""
    [Requirement Analysis]
    User Intent: {requirement_analysis.get('user_intent', 'N/A')}
    Required Features: {json.dumps(requirement_analysis.get('required_features', []), ensure_ascii=False)}
    """

    user_prompt = f"""
    User Query: "{user_query}"
    {analysis_summary}
    [Graph Context (Facts)]
    - Target Component: {anchor_name}
    - Available Parts (Sub-components with full metadata): {json.dumps(retrieved_children, ensure_ascii=False, indent=2)}
    
    [Component Information]
    Each part includes:
    - type: Component type name
    - label: Human-readable label
    - propType: HTML element type (if applicable)
    - propSchema: Available properties with types, defaults, and descriptions
    - validationRules: Input validation rules (pattern, minLength, etc.)
    - layoutType: Layout system (flex, grid, etc.)
    - flexDirection: Flex direction (row, column)
    - spacing: Spacing between children
    - ariaLabel: Accessibility label
    - role: ARIA role
    - defaultState: Default component state
    - variant: Style variant
    
    [Constraints]
    - {", ".join(constraints) if constraints else "None"}
    
    Generate the UI JSON spec now. Use all available metadata and requirement analysis to create a complete and accessible component specification that matches the user's intent.
    """

    response = self.client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"} 
    )

    llm_output = json.loads(response.choices[0].message.content)

    return {
        "source_anchor": anchor_name,
        "reasoning_mode": context_mode,
        "generated_spec": llm_output,
        "requirement_analysis": requirement_analysis
    }

  def is_user_data_loaded(self) -> bool:
    """사용자 데이터가 로드되어 있는지 확인"""
    if self.user_data_loaded:
      return True
    
    # SPARQL 쿼리로 GRAPH_USER에 데이터가 있는지 확인
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT (COUNT(?s) as ?count) WHERE {
      ?s rdfs:label ?label .
    }
    LIMIT 1
    """
    
    results = self.store.query(query)
    # 온톨로지 노드 개수와 비교하여 사용자 데이터가 있는지 확인
    # 간단하게는 플래그로 관리
    return self.user_data_loaded

  def load_user_data_from_string(self, ttl_string: str, base_iri: str = "http://myapp.com/ui/") -> dict:
    """API로 받은 문자열 데이터를 User Graph에 적재"""
    try:
      # 기존 사용자 데이터 삭제 (재연결 시 중복 방지)
      # pyoxigraph에서는 그래프를 직접 삭제할 수 없으므로
      # 모든 트리플을 쿼리해서 삭제하거나, 새 Store를 만들거나
      # 여기서는 간단하게 기존 데이터를 무시하고 새로 로드
      # (실제로는 사용자 데이터만 쿼리해서 삭제하는 것이 좋지만, 
      #  현재는 전체 인덱스를 재빌드하는 방식으로 처리)
      
      # TTL 문자열을 바이트로 변환
      ttl_bytes = ttl_string.encode('utf-8')
      
      # 사용자 데이터 로드 (기본 그래프에 로드, 나중에 쿼리로 구분)
      self.store.load(ttl_bytes, "text/turtle", base_iri=base_iri)
      
      # 플래그 설정
      self.user_data_loaded = True
      
      # 인덱스 재빌드 (새로운 데이터 검색 가능하게)
      self._build_index()
      
      node_count = len(self.nodes)
      return {
          "success": True,
          "node_count": node_count,
          "message": f"User data loaded successfully! ({node_count} total nodes)"
      }
    except Exception as e:
      raise ValueError(f"Failed to load user data: {str(e)}")

  def connect_user_data(self, ttl_string: str, base_iri: str = "http://myapp.com/ui/") -> dict:
    """
    초기 연동을 위한 통합 API 함수
    
    Returns:
        dict: {
            "status": "success" | "already_connected",
            "node_count": int,
            "message": str
        }
    """
    # 이미 연결되어 있는지 확인
    if self.is_user_data_loaded():
      # 현재 노드 개수 반환
      node_count = len(self.nodes)
      return {
          "status": "already_connected",
          "node_count": node_count,
          "message": f"Already connected! ({node_count} nodes available)"
      }
    
    # 사용자 데이터 로드
    result = self.load_user_data_from_string(ttl_string, base_iri)
    
    return {
        "status": "success",
        "node_count": result["node_count"],
        "message": result["message"]
    }