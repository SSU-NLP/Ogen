import pyoxigraph
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import openai  # LLM 클라이언트 추가
import json

class OgenEngine:
  def __init__(self, ttl_path: str, openai_api_key: str): # API Key 추가
    
    self.client = openai.OpenAI(api_key=openai_api_key) # LLM 클라이언트 초기화

    self.store = pyoxigraph.Store()

    if ttl_path is None:
        base_dir = Path(__file__).parent
        ttl_path = base_dir / "data" / "knowledge.ttl"

    try:
      with open(ttl_path, "rb") as f:
        self.store.load(f, "text/turtle", base_iri="http://ogen.ai/ontology/")
      print("Ontology Loaded!")
    except FileNotFoundError:
      print(f"❌ Error: {ttl_path} not found")
      raise

    self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
    self.nodes = []
    self.node_embeddings = []
    self._build_index()
  
  # ... (기존 _build_index, find_anchor_node 메서드는 동일) ...
  def _build_index(self):
    """Embed all nodes in the graph"""

    query = """
    PREFIX ex: <http://ogen.ai/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?s ?label ?comment ?keywords WHERE {
      ?s rdfs:label ?label .
      OPTIONAL { ?s rdfs:comment ?comment }
      OPTIONAL { ?s ex:keywords ?keywords }
    }
    """

    results = self.store.query(query)

    for binding in results:
      uri = binding["s"].value
      label = binding["label"].value
      search_text = f"{label}"
      if "keywords" in binding:
          search_text += f" {binding['keywords'].value}"
      if "comment" in binding:
            search_text += f" {binding['comment'].value}"
      
      # 임베딩은 search_text로 수행
      self.nodes.append({
          "uri": uri, 
          "label": label, 
          "search_text": search_text 
      })
       
    
    # print(f"📊 Indexed Nodes: {[n['label'] for n in self.nodes]}") # 로그 너무 길면 주석 처리

    if self.nodes:
      labels = [n["label"] for n in self.nodes]
      self.node_embeddings = self.embedder.encode(labels)

  def find_anchor_node(self, user_query: str):
    """Find the anchor node for the user query"""
    if not self.nodes:
      return None

    query_vec = self.embedder.encode([user_query])
    similarities = cosine_similarity(query_vec, self.node_embeddings)[0]
    best_idx = np.argmax(similarities)
    best_node = self.nodes[best_idx]
    
    print(f"📊 Best Node: {best_node}")

    # 임계값 설정 (너무 관련 없는 경우 필터링)
    if similarities[best_idx] < 0.3:
        return None

    return best_node["uri"]
  def get_subgraph_context(self, anchor_uri: str):
    # ... (기존과 동일) ...
    anchor_sparql_ref = f"<{anchor_uri}>" if not anchor_uri.startswith("<") else anchor_uri

    query = f"""
    PREFIX ex: <http://ogen.ai/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?part ?label ?propType WHERE {{
      {anchor_sparql_ref} ex:hasPart ?part .
      ?part rdfs:label ?label .
      OPTIONAL {{ ?part ex:propType ?propType }}
    }}
    """
    
    results = self.store.query(query)
    parts = []
    for binding in results:
      part_uri = binding["part"].value
      parts.append({
        "type": part_uri.split("/")[-1], # URI의 마지막 부분을 타입으로 사용
        "label": binding["label"].value,
        "propType": binding["propType"].value if binding["propType"] else "string"
      })
    return parts
  def find_anchor_node_with_llm(self, user_query: str, top_k: int = 5):
    """
    [Agentic Selection Step]
    1. Vector Search로 후보군(Candidates)을 좁힘 (Pre-filtering)
    2. LLM이 후보군 중에서 사용자의 의도에 가장 적합한 앵커를 선택 (Reasoning)
    """
    if not self.nodes:
      return None

    # 1. Vector Search (Retrieve Top-K)
    query_vec = self.embedder.encode([user_query])
    similarities = cosine_similarity(query_vec, self.node_embeddings)[0]
    
    # 상위 K개의 인덱스 추출
    top_k_indices = np.argsort(similarities)[::-1][:top_k]
    
    candidates = []
    for idx in top_k_indices:
      node = self.nodes[idx]
      score = similarities[idx]
      candidates.append({
          "uri": node["uri"], 
          "label": node["label"], 
          "score": float(score) # JSON 직렬화를 위해 float 변환
      })

    print(f"🕵️ Candidates found: {[c['label'] for c in candidates]}")

    # 2. LLM Reasoning (Selector Agent)
    # 문맥상 가장 적절한 녀석을 LLM이 선택하게 함
    system_prompt = """
    You are a semantic router for a UI Knowledge Graph.
    Select the most appropriate 'Target Component' URI from the candidates based on the user's intent.
    If none of the candidates are suitable, return null.
    
    IMPORTANT: You must return the result in pure JSON format.
    Output Schema: {"selected_uri": "string" or null, "reason": "string"}
    """

    user_prompt = f"""
    User Query: "{user_query}"
    
    Candidates:
    {json.dumps(candidates, ensure_ascii=False, indent=2)}
    
    Select the best anchor node and return JSON.
    """

    response = self.client.chat.completions.create(
        model="gpt-4o-mini", # 판단만 하는 거라 가벼운 모델도 OK
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
    1. Retrieve Graph Context (Facts)
    2. Construct Prompt (Instruction + Facts)
    3. Generate Output (LLM Inference)
    """

    # 1. Retrieval + Selection (변경된 메서드 호출)
    anchor_uri = self.find_anchor_node_with_llm(user_query)
    
    if not anchor_uri:
      # LLM이 "관련된 게 없다"고 판단한 경우
      return {"error": "요청하신 UI 컴포넌트를 지식 그래프에서 찾을 수 없습니다."}
        
    anchor_name = anchor_uri.split("/")[-1]
    
    # 2. Graph Expansion (선택된 앵커 기준으로 팩트 조회)
    retrieved_children = self.get_subgraph_context(anchor_uri)
    
    # 상황별 제약조건 설정 (이 부분도 추후엔 LLM이 판단하게 할 수 있음)
    constraints = []
    if context_mode == "low-vision":
      constraints = ["High Contrast Theme", "Base Font Size 24px"]

    system_prompt = f"""
    You are an expert UI Compiler powered by a Knowledge Graph.
    Generate a JSON specification for a UI component based on the request.
    
    Target: {anchor_name}
    Available Parts: {json.dumps(retrieved_children, ensure_ascii=False)}
    """
    # 2. Prompt Engineering (Context Injection)
    # LLM에게 그래프 데이터를 문맥으로 제공합니다.
    system_prompt = f"""
    You are an expert UI Compiler powered by a Knowledge Graph.
    Your job is to generate a JSON specification for a UI component based on the user's request.
    
    [RULES]
    1. STRICTLY use only the child components provided in the 'Graph Context'. Do not hallucinate new components.
    2. Apply the 'Constraints' to the properties of the components.
    3. Output must be valid JSON.
    """

    user_prompt = f"""
    User Query: "{user_query}"
    
    [Graph Context (Facts)]
    - Target Component: {anchor_name}
    - Available Parts (Sub-components): {json.dumps(retrieved_children, ensure_ascii=False)}
    
    [Constraints]
    - {", ".join(constraints) if constraints else "None"}
    
    Generate the UI JSON spec now.
    """

    # 3. Generation (LLM Call)
    response = self.client.chat.completions.create(
        model="gpt-4o-mini", # 혹은 gpt-3.5-turbo, fine-tuned model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"} # JSON 모드 강제
    )

    llm_output = json.loads(response.choices[0].message.content)

    return {
        "source_anchor": anchor_name,
        "reasoning_mode": context_mode,
        "generated_spec": llm_output
    }