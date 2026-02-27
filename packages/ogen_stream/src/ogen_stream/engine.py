import pyoxigraph
from pyoxigraph import Store, NamedNode, RdfFormat
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from jsonschema import Draft7Validator
import numpy as np
import openai
import json
import os
from pathlib import Path


class OgenEngine:
    def __init__(
        self,
        openai_api_key: str,
        persistence_dir: str = "./ogen_data",
        openai_base_url: str | None = None,
        model_config: dict[str, str] | None = None,
        model_config_path: str | None = None,
    ):
        self.client = openai.OpenAI(api_key=openai_api_key, base_url=openai_base_url)
        self.persistence_dir = Path(persistence_dir)
        self.persistence_dir.mkdir(exist_ok=True)
        self.model_config = self._load_model_config(model_config, model_config_path)

        self._store_lock = None

        # Try to load existing graph from disk (dataset formats)
        graph_file_trig = self.persistence_dir / "user_graph.trig"
        graph_file_legacy_ttl = self.persistence_dir / "user_graph.ttl"

        self.store = Store()
        self.user_data_loaded = False

        # Load persisted user graph (preferred: TriG). Fallback: legacy Turtle if present.
        if graph_file_trig.exists() and graph_file_trig.stat().st_size > 0:
            try:
                with open(graph_file_trig, "rb") as f:
                    self.store.load(f, RdfFormat.TRIG, base_iri="http://myapp.com/ui/")
                print("✅ Loaded persisted graph from disk (TriG)")
                self.user_data_loaded = True
            except Exception as e:
                print(f"⚠️ Failed to load persisted TriG graph, ignoring: {e}")
                self.store = Store()
                self.user_data_loaded = False
        elif (
            graph_file_legacy_ttl.exists() and graph_file_legacy_ttl.stat().st_size > 0
        ):
            try:
                with open(graph_file_legacy_ttl, "rb") as f:
                    self.store.load(f, "text/turtle", base_iri="http://myapp.com/ui/")
                print("✅ Loaded persisted graph from disk (legacy Turtle)")
                self.user_data_loaded = True
            except Exception as e:
                print(f"⚠️ Failed to load legacy Turtle graph, ignoring: {e}")
                self.store = Store()
                self.user_data_loaded = False

        self.GRAPH_CORE = NamedNode("http://ogen.ai/graph/core")
        self.GRAPH_USER = NamedNode("http://ogen.ai/graph/user")
        self.GRAPH_CONTEXT = NamedNode("http://ogen.ai/graph/context")

        # Ontology file path (inside package)
        current_dir = Path(__file__).parent
        ontology_path = current_dir / "ogen-core.ttl"

        try:
            with open(ontology_path, "rb") as f:
                # pyoxigraph's load loads into the default graph by default
                # To use Named Graphs, use FROM clause in queries
                self.store.load(f, "text/turtle", base_iri="http://ogen.ai/ontology/")
            print("✅ Ontology Loaded from package!")
        except FileNotFoundError:
            print(f"❌ Error: {ontology_path} not found")
            raise

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.nodes = []
        self.node_embeddings = []

        self._build_index()

        # Initialize lock lazily (avoid importing asyncio in all contexts)
        try:
            import threading

            self._store_lock = threading.Lock()
        except Exception:
            self._store_lock = None

    def _load_model_config(
        self,
        model_config: dict[str, str] | None,
        model_config_path: str | None,
    ) -> dict[str, str]:
        defaults = {
            "analysis": "gpt-5",
            "anchor": "gpt-4o-mini",
            "generation": "gpt-5",
            "pruning": "gpt-5-mini",
        }

        config: dict[str, str] = {**defaults}

        if model_config_path:
            try:
                with open(model_config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    for key, value in loaded.items():
                        if isinstance(key, str) and isinstance(value, str) and value:
                            config[key] = value
            except Exception as e:
                print(f"⚠️ Failed to load model config JSON: {e}")

        if model_config:
            for key, value in model_config.items():
                if isinstance(key, str) and isinstance(value, str) and value:
                    config[key] = value

        return config

    def _build_index(self):
        """Embed all nodes in the graph (unified search across GRAPH_CORE + GRAPH_USER)"""

        query = """
    PREFIX ex: <http://ogen.ai/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?s ?label ?comment ?keywords WHERE {
      ?s rdfs:label ?label .
      OPTIONAL { ?s rdfs:comment ?comment }
      OPTIONAL { ?s ex:keywords ?keywords }
    }
    """

        # Reset existing index
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

            self.nodes.append({"uri": uri, "label": label, "search_text": search_text})

        if self.nodes:
            labels = [n["label"] for n in self.nodes]
            self.node_embeddings = self.embedder.encode(labels)
            print(f"📊 Index rebuilt: {len(self.nodes)} nodes")

    def get_subgraph_context(
        self,
        anchor_uri: str,
        user_query: str = "",
        requirement_analysis: dict | None = None,
        max_depth: int = 2,
    ):
        """
        [Graph Traversal Step]
        Dynamically traverse Subgraph Context using BFS/DFS.
        Removes hardcoded properties (Layout_intents) and retrieves all properties from the knowledge graph.

        [Agentic Pruning]
        When user_query and requirement_analysis are provided,
        prunes irrelevant child nodes via LLM.
        """
        visited = set()
        queue = [(anchor_uri, 0)]  # (uri, depth)
        subgraph = {}

        # Pruning Threshold: LLM intervenes only when children exceed this count (saves tokens)
        pruning_threshold = 3

        while queue:
            current_uri, depth = queue.pop(0)  # BFS

            if current_uri in visited:
                continue
            visited.add(current_uri)

            # Retrieve node basic information
            node_info = self._get_node_properties(current_uri)
            subgraph[current_uri] = node_info

            # Pruning & Depth Limit
            if depth >= max_depth:
                continue

            # Traverse child nodes (e.g., hasPart relations)
            # Retrieve all children
            children = self._get_children(current_uri)

            # [Agentic Pruning Implementation]
            # Perform LLM filtering when depth is 0 (i.e., direct children of anchor) or when there are too many children
            if (
                user_query
                and children
                and (len(children) >= pruning_threshold or depth == 0)
            ):
                print(
                    f"🤖 Agentic Pruning triggered for {current_uri} ({len(children)} children)"
                )
                filtered_children = self._agentic_filter_children(
                    current_uri, children, user_query, requirement_analysis
                )
                print(f"✂️ Pruned: {len(children)} -> {len(filtered_children)} nodes")
                children = filtered_children
            for child_uri in children:
                if child_uri not in visited:
                    queue.append((child_uri, depth + 1))

        # Format results (convert to list)
        return list(subgraph.values())

    def _agentic_filter_children(
        self,
        parent_uri: str,
        children_uris: list,
        user_query: str,
        requirement_analysis: dict | None,
    ) -> list:
        """
        [Agentic Pruning Core]
        Shows the list of child nodes to LLM and selects only those matching user intent.
        """
        if not children_uris:
            return []

        # Pre-fetch label information for child nodes (LLM may struggle to judge from URIs alone)
        candidates = []
        for uri in children_uris:
            props = self._get_node_properties(uri)
            candidates.append(
                {
                    "uri": uri,
                    "label": props.get("label", uri.split("/")[-1]),
                    "description": props.get("comment", ""),
                }
            )

        analysis_context = ""
        if requirement_analysis:
            analysis_context = f"""
    User Intent: {requirement_analysis.get("user_intent", "N/A")}
    Required Features: {json.dumps(requirement_analysis.get("required_features", []), ensure_ascii=False)}
    """

        system_prompt = """
    You are a Knowledge Graph Pruning Agent.
    Your task is to filter a list of child components and keep ONLY those that are relevant to the user's request.

    [Rules]
    1. Select components that are necessary to fulfill the user's intent.
    2. If a component is a container or structural element (like 'Wrapper', 'Section'), keep it to maintain layout.
    3. Remove components that are clearly irrelevant (e.g., 'MarketingBanner' when user asks for 'Settings').
    4. Return the list of selected URIs in JSON format.

    Output Schema: {"selected_uris": ["uri1", "uri2"]}
    """

        user_prompt = f"""
    User Query: "{user_query}"
    {analysis_context}

    Parent Component: {parent_uri}

    Candidates (Children):
    {json.dumps(candidates, ensure_ascii=False, indent=2)}

    Select relevant children URIs.
    """

        try:
            response = self.client.chat.completions.create(
                model=self.model_config.get("pruning", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content or "{}")
            selected = result.get("selected_uris", [])

            # Filter to only URIs that actually exist in the input (sanity check)
            valid_selected = [uri for uri in selected if uri in children_uris]

            # If LLM selected nothing, it could mean overly aggressive pruning.
            # Options: return original list (conservative) or empty list (aggressive).
            # Here we assume LLM judged nothing as essential, so empty list is valid,
            # but as a fallback at least 1 item might be kept for safety.
            # For now, return as-is.
            return valid_selected

        except Exception as e:
            print(f"⚠️ Agentic pruning failed: {e}. Returning all children.")
            return children_uris

    def _get_node_properties(self, uri: str) -> dict:
        """Dynamically retrieve all properties of a single node (no hardcoding)"""
        sparql_ref = f"<{uri}>" if not uri.startswith("<") else uri

        query = f"""
        SELECT ?p ?o WHERE {{
            {sparql_ref} ?p ?o .
        }}
        """
        results = self.store.query(query)
        # Provide a stable component id for UI compilation.
        # This should match the frontend registry key (e.g., "LoginCard").
        raw_uri = uri[1:-1] if uri.startswith("<") and uri.endswith(">") else uri
        component_id = raw_uri.split("#")[-1].split("/")[-1]
        properties = {"uri": uri, "id": component_id}

        for binding in results:
            p_val = binding["p"].value
            o_val = binding["o"].value

            # Extract property name (last part of URI)
            prop_name = p_val.split("/")[-1].split("#")[-1]

            # Attempt JSON parsing (for complex data like Schema or Rules)
            try:
                import json

                parsed_value = json.loads(o_val)
            except:
                parsed_value = o_val

            properties[prop_name] = parsed_value

        return properties

    def _get_children(self, parent_uri: str) -> list:
        """Retrieve child node URIs (hasPart, etc.)"""
        sparql_ref = f"<{parent_uri}>" if not parent_uri.startswith("<") else parent_uri

        query = f"""
        PREFIX ex: <http://ogen.ai/ontology/>
        SELECT ?child WHERE {{
            {sparql_ref} ex:hasPart ?child .
        }}
        """
        results = self.store.query(query)
        return [binding["child"].value for binding in results]

    def analyze_requirement(self, user_query: str) -> dict:
        """
        [Requirement Analysis Step]
        Analyze user request to identify required UI components and features

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
            model=self.model_config.get("analysis", "gpt-5"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        analysis = json.loads(response.choices[0].message.content or "{}")
        print(
            f"📋 Requirement Analysis: {json.dumps(analysis, ensure_ascii=False, indent=2)}"
        )

        return analysis

    def find_anchor_node_with_llm(
        self, user_query: str, requirement_analysis: dict | None = None, top_k: int = 5
    ):
        """
        [Agentic Selection Step]
        1. Narrow candidates via Vector Search (Pre-filtering)
        2. LLM selects the most suitable anchor from candidates based on user intent (Reasoning)

        Args:
            user_query: User request
            requirement_analysis: Result of analyze_requirement (optional, enables more accurate search)
            top_k: Number of candidates to search
        """
        if not self.nodes:
            return None

        # If requirement analysis result exists, use suggested_anchor as keyword
        search_query = user_query
        if requirement_analysis and requirement_analysis.get("suggested_anchor"):
            search_query = f"{user_query} {requirement_analysis['suggested_anchor']}"
            # Also add keywords from required_components
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
            candidates.append(
                {"uri": node["uri"], "label": node["label"], "score": float(score)}
            )

        print(f"🕵️ Candidates found: {[c['label'] for c in candidates]}")

        # Include requirement analysis result in prompt
        analysis_context = ""
        if requirement_analysis:
            analysis_context = f"""
            [Requirement Analysis]
            User Intent: {requirement_analysis.get("user_intent", "N/A")}
            Required Components: {json.dumps(requirement_analysis.get("required_components", []), ensure_ascii=False)}
            Suggested Anchor: {requirement_analysis.get("suggested_anchor", "N/A")}
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
            model=self.model_config.get("anchor", "gpt-5"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        decision = json.loads(response.choices[0].message.content or "{}")

        selected_uri = decision.get("selected_uri")
        print(f"🎯 LLM Selected: {selected_uri} (Reason: {decision.get('reason')})")

        return selected_uri

    def reason(self, user_query: str, context_mode: str = "default"):
        """
        LLM Reasoning Stage:
        1. Analyze User Requirement
        2. Find Anchor Node based on Analysis (KG-based reasoning)
        3. Retrieve Graph Context (Facts)
        4. Construct Prompt (Instruction + Facts + Analysis)
        5. Generate Output (LLM Inference)
        """

        print(f"🔍 Step 1: Analyzing requirement for query: '{user_query}'")
        requirement_analysis = self.analyze_requirement(user_query)


        print(f"🔍 Step 2: Finding anchor node based on analysis")
        anchor_uri = self.find_anchor_node_with_llm(user_query, requirement_analysis)

        if not anchor_uri:
            suggested_anchor = None
            if requirement_analysis:
                suggested_anchor = requirement_analysis.get("suggested_anchor")

            return {
                "error": "No valid anchor node was found in the knowledge graph.",
                "reason": "Closed-world synthesis requires a registry-backed KG anchor.",
                "user_query": user_query,
                "suggested_anchor": suggested_anchor,
                "requirement_analysis": requirement_analysis,
            }

        print(f"📚 Step 3: Retrieving graph context for anchor: {anchor_uri}")
        retrieved_children = self.get_subgraph_context(
            anchor_uri,
            user_query=user_query,
            requirement_analysis=requirement_analysis,
        )

        if not retrieved_children:
            return {
                "error": "No usable subgraph context was retrieved from the knowledge graph.",
                "reason": "Closed-world synthesis requires KG-backed component context.",
                "source_anchor": anchor_uri,
                "user_query": user_query,
                "requirement_analysis": requirement_analysis,
            }

        # Step 4 & 5: Generate UI with retrieved KG context only
        return self._generate_ui_with_context(
            user_query,
            requirement_analysis,
            anchor_uri,
            retrieved_children,
            context_mode,
        )

    def _generate_ui_with_context(
        self,
        user_query: str,
        requirement_analysis: dict,
        anchor_name: str,
        retrieved_children: list,
        context_mode: str,
    ) -> dict:
        """
        Generate UI using Graph Context with iterative validation.
        """
        constraints = []
        if context_mode == "low-vision":
            constraints = ["High Contrast Theme", "Base Font Size 24px"]

        allowed_component_ids = [
            (c.get("id") or c.get("type") or c.get("label"))
            for c in retrieved_children
            if isinstance(c, dict)
        ]
        allowed_component_ids = [cid for cid in allowed_component_ids if cid]

        if not allowed_component_ids:
            return {
                "error": "No allowed component IDs were found in the retrieved graph context.",
                "reason": "Closed-world synthesis requires non-empty KG-backed component candidates.",
                "source_anchor": anchor_name,
                "requirement_analysis": requirement_analysis,
            }

        allowed_component_ids_set = set(allowed_component_ids)
        schema_map = self._build_component_schema_map(retrieved_children)

        anchor_id = str(anchor_name).split("#")[-1].split("/")[-1]

        system_prompt = f"""
            You are an expert UI Compiler powered by a Knowledge Graph.
            Your job is to generate a JSON specification for a UI component based on the user's request.

            [RULES]
            0. The JSON field "type" MUST be a component id, not a label. Use ONLY ids from AllowedComponentIds.
            1. STRICTLY use only the components provided in the 'Graph Context'. Do not hallucinate new components.
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
            User Intent: {requirement_analysis.get("user_intent", "N/A")}
            Required Features: {json.dumps(requirement_analysis.get("required_features", []), ensure_ascii=False)}
            """

        base_user_prompt = f"""
            User Query: "{user_query}"
            {analysis_summary}
            [Graph Context (Facts)]
            - Target Component URI: {anchor_name}
            - Target Component Id: {anchor_id}
            - AllowedComponentIds: {json.dumps(allowed_component_ids, ensure_ascii=False)}
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

        max_attempts = 3
        repair_feedback = ""
        last_errors = []
        llm_output = {}

        for attempt in range(1, max_attempts + 1):
            user_prompt = base_user_prompt

            if repair_feedback:
                user_prompt += f"""

    [Validation Errors from Previous Attempt]
    {repair_feedback}

    Revise the entire JSON output so that it satisfies all listed constraints and schema requirements.
    """

            response = self.client.chat.completions.create(
                model=self.model_config.get("generation", "gpt-5"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )

            llm_output = json.loads(response.choices[0].message.content or "{}")

            validation_errors = self._validate_ui_tree(
                llm_output,
                allowed_component_ids_set,
                schema_map,
            )

            if not validation_errors:
                return {
                    "source_anchor": anchor_name,
                    "reasoning_mode": context_mode,
                    "generated_spec": llm_output,
                    "requirement_analysis": requirement_analysis,
                    "validated": True,
                    "validation_attempts": attempt,
                }

            last_errors = validation_errors
            repair_feedback = "\n".join(f"- {e}" for e in validation_errors[:20])

        return {
            "error": "Failed to generate a valid UI specification within retry limit.",
            "reason": "Iterative validation failed after 3 attempts.",
            "source_anchor": anchor_name,
            "reasoning_mode": context_mode,
            "generated_spec": llm_output,
            "requirement_analysis": requirement_analysis,
            "validated": False,
            "validation_attempts": max_attempts,
            "validation_errors": last_errors,
        }

    def is_user_data_loaded(self) -> bool:
        """Check if user data is loaded"""
        if self.user_data_loaded:
            return True

        # Check if GRAPH_USER has data via SPARQL query
        query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT (COUNT(?s) as ?count) WHERE {
      ?s rdfs:label ?label .
    }
    LIMIT 1
    """

        results = self.store.query(query)
        # Compare with ontology node count to check if user data exists
        # Managed simply via flag
        return self.user_data_loaded

    def load_user_data_from_string(
        self, ttl_string: str, base_iri: str = "http://myapp.com/ui/"
    ) -> dict:
        """Load string data received via API into User Graph"""
        try:
            # Delete existing user data (prevent duplication on reconnect)
            # pyoxigraph cannot directly delete a graph,
            # so either query and delete all triples, or create a new Store.
            # Here we simply ignore existing data and reload.
            # (Ideally, only user data should be queried and deleted,
            #  but currently handled by rebuilding the entire index)

            # Convert TTL string to bytes
            ttl_bytes = ttl_string.encode("utf-8")

            # Load user data (into default graph, distinguished later by query)
            self.store.load(ttl_bytes, "text/turtle", base_iri=base_iri)

            # Set flag
            self.user_data_loaded = True

            # Rebuild index (enable searching new data)
            self._build_index()

            node_count = len(self.nodes)
            return {
                "success": True,
                "node_count": node_count,
                "message": f"User data loaded successfully! ({node_count} total nodes)",
            }
        except Exception as e:
            raise ValueError(f"Failed to load user data: {str(e)}")

    def connect_user_data(
        self,
        ttl_string: str,
        base_iri: str = "http://myapp.com/ui/",
        force: bool = False,
    ) -> dict:
        """
        Unified API function for initial connection

        Returns:
            dict: {
                "status": "success" | "already_connected",
                "node_count": int,
                "message": str
            }
        """
        # Already connected: be idempotent unless force is requested
        if self.is_user_data_loaded() and not force:
            node_count = len(self.nodes)
            return {
                "status": "already_connected",
                "node_count": node_count,
                "message": f"Already connected! ({node_count} nodes available)",
            }

        # Rebuild store safely for force reconnect to avoid mixing old and new data.
        if force:
            if self._store_lock:
                with self._store_lock:
                    result = self._rebuild_store_with_user_data(ttl_string, base_iri)
            else:
                result = self._rebuild_store_with_user_data(ttl_string, base_iri)
        else:
            result = self.load_user_data_from_string(ttl_string, base_iri)

        # Persist graph to disk (for restoration on next startup)
        self._persist_graph()

        return {
            "status": "success",
            "node_count": result["node_count"],
            "message": result["message"],
        }

    def _persist_graph(self):
        """Persist current graph state to disk"""
        try:
            graph_file = self.persistence_dir / "user_graph.trig"
            tmp_file = self.persistence_dir / "user_graph.trig.tmp"
            print(f"📝 Attempting to persist graph to {graph_file}")

            # Check if store has any data
            if not self.store:
                print("❌ Store is None, cannot persist")
                return

            with open(tmp_file, "wb") as f:
                # Store.dump serializes datasets; TriG is the preferred dataset format.
                self.store.dump(f, RdfFormat.TRIG)
                print("✅ TriG format succeeded")

            tmp_file.replace(graph_file)

            # Verify file was written
            file_size = graph_file.stat().st_size
            print(f"✅ Graph persisted to {graph_file} ({file_size} bytes)")
        except Exception as e:
            print(f"❌ Failed to persist graph: {e}")
            import traceback

            traceback.print_exc()

    def _rebuild_store_with_user_data(self, ttl_string: str, base_iri: str) -> dict:
        """Rebuild Store from scratch (ontology + user ttl) and swap atomically."""

        # Build a new store in isolation
        new_store = Store()
        current_dir = Path(__file__).parent
        ontology_path = current_dir / "ogen-core.ttl"

        with open(ontology_path, "rb") as f:
            new_store.load(f, "text/turtle", base_iri="http://ogen.ai/ontology/")

        ttl_bytes = ttl_string.encode("utf-8")
        new_store.load(ttl_bytes, "text/turtle", base_iri=base_iri)

        # Swap in new store and rebuild index
        old_store = self.store
        old_loaded = self.user_data_loaded
        try:
            self.store = new_store
            self.user_data_loaded = True
            self._build_index()
            node_count = len(self.nodes)
            return {
                "success": True,
                "node_count": node_count,
                "message": f"User data loaded successfully! ({node_count} total nodes)",
            }
        except Exception:
            self.store = old_store
            self.user_data_loaded = old_loaded
            raise
    
    def _build_component_schema_map(self, retrieved_children: list) -> dict:
        schema_map = {}
        for c in retrieved_children:
            if not isinstance(c, dict):
                continue

            cid = c.get("id") or c.get("type") or c.get("label")
            prop_schema = c.get("propSchema")

            if cid and isinstance(prop_schema, dict):
                schema_map[cid] = prop_schema

        return schema_map


    def _validate_ui_tree(
        self,
        node: dict,
        allowed_component_ids: set[str],
        schema_map: dict,
        path: str = "root",
    ) -> list[str]:
        errors = []

        if not isinstance(node, dict):
            return [f"{path}: node must be an object"]

        node_type = node.get("type")
        props = node.get("props")
        children = node.get("children", [])

        # Basic structural checks
        if not isinstance(node_type, str):
            errors.append(f"{path}: 'type' must be a string")
            return errors

        if node_type not in allowed_component_ids:
            errors.append(
                f"{path}: component '{node_type}' is not included in AllowedComponentIds"
            )

        if props is None:
            errors.append(f"{path}: missing 'props'")
        elif not isinstance(props, dict):
            errors.append(f"{path}: 'props' must be an object")

        if children is None:
            children = []
        elif not isinstance(children, list):
            errors.append(f"{path}: 'children' must be a list")
            children = []

        # Per-component propSchema validation
        if isinstance(props, dict) and node_type in schema_map:
            schema = schema_map[node_type]
            validator = Draft7Validator(schema)
            for err in validator.iter_errors(props):
                loc = ".".join(str(x) for x in err.path) if err.path else "props"
                errors.append(f"{path}: schema violation at {loc}: {err.message}")

        # Recursive validation
        for i, child in enumerate(children):
            errors.extend(
                self._validate_ui_tree(
                    child,
                    allowed_component_ids,
                    schema_map,
                    path=f"{path}.children[{i}]",
                )
            )

        return errors