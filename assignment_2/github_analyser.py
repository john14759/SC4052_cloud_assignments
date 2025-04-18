import os
import streamlit as st
import requests
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import datetime

def init():
    print("Setting Up.....")
    load_dotenv(override=True)
    st.session_state.llm = AzureChatOpenAI(
        azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
        api_key=os.environ['AZURE_OPENAI_APIKEY'],
        deployment_name=os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'],
        model_name=os.environ['AZURE_OPENAI_MODEL_NAME'],
        api_version=os.environ['AZURE_OPENAI_API_VERSION'],
        temperature=0.7
    )

    st.session_state.HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {os.environ['GITHUB_API_KEY']}",
    "X-GitHub-Api-Version": "2022-11-28"
    }

    st.session_state.GITHUB_API_URL = os.environ['GITHUB_API_URL']

    if 'analysis_type' not in st.session_state:
        st.session_state.analysis_type = "Documentation"
    if 'prompt_complexity' not in st.session_state:
        st.session_state.prompt_complexity = "basic"


    st.session_state.DOCUMENTATION_PROMPTS = {
        "basic": """Generate comprehensive documentation for this code.""",
        
        "detailed": """Generate comprehensive documentation for this code. 
                    Include: 
                    1. Purpose and functionality
                    2. Key functions/classes
                    3. Input/output specifications
                    4. Usage examples""",
                    
        "advanced": """As an expert developer and technical writer, generate thorough documentation for this code.
                    Include:
                    1. Executive summary of purpose and functionality
                    2. Detailed breakdown of architecture and design patterns
                    3. Complete API reference for all functions/classes/methods
                    4. Input/output specifications with data types and constraints
                    5. Error handling approach and edge cases
                    6. Usage examples with expected outputs
                    7. Dependencies and requirements
                    8. Potential optimization opportunities
                    """
    }

    st.session_state.AI_DETECTION_PROMPTS = {
        "basic": """Analyze this code for signs of AI generation.""",
        
        "detailed": """
                    Analyze this code for signs of AI generation. Consider:
                    1. Code structure patterns
                    2. Common AI-generated code characteristics
                    3. Documentation quality
                    4. Style consistency
                    """,
                    
        "advanced": """
                    As an expert in code analysis and AI-generated content detection, thoroughly examine this code for hallmarks of AI generation.
                    Analyze the following aspects and provide a confidence score (0-100%) for each:

                    1. Structural fingerprints:
                        - Overly consistent formatting that lacks human variability
                        - Unnaturally regular comment patterns and documentation
                        - Excessive or redundant error handling
                    
                    2. Stylistic indicators:
                        - Variable naming conventions that are too consistent or follow textbook patterns
                        - Lack of developer shortcuts or "quirks" found in human code
                        - Unnatural comment-to-code ratio
                    
                    3. Logical patterns:
                        - Solutions that follow common tutorial examples too closely
                        - Implementations that prioritize readability over efficiency
                        - Overly abstracted or generalized solutions when specificity would be more appropriate
                    
                    4. Technical hallmarks:
                        - Implementation approaches that align with common LLM training data
                        - Inclusion of explanatory comments that a human developer wouldn't typically include
                        - Missing domain-specific optimizations that human experts would implement
                    
                    Conclude with an overall assessment of whether this code was likely AI-generated,
                    partially AI-assisted, or human-written, with an overall confidence score.
                    """
    }

def search_github_code(query):
    params = {"q": query}
    
    try:
        response = requests.get(st.session_state.GITHUB_API_URL, params=params, headers=st.session_state.HEADERS)
        response.raise_for_status()
        print(response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"GitHub API Error: {str(e)}")
        return None

def analyze_with_llm(code_snippet, prompt):
    
    try:
        response = st.session_state.llm.invoke(f"{prompt}\n\n{code_snippet}")
        return response.content
    except Exception as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return None

def main():
    st.set_page_config(layout="wide")
    st.title("GitHub Code Analyzer SaaS")
    init()
    
    
    # Tabs for different sections
    tab1, tab2 = st.tabs(["Code Analysis", "Prompt Engineering"])
    
    with tab2:  # Prompt Engineering tab
        st.header("Prompt Engineering Lab")
        st.write("Experiment with different prompts to optimize code analysis results")
        
        # Store selections in session state
        st.session_state.analysis_type = st.radio(
            "Analysis Type", 
            ["Documentation", "AI Detection"],
            index=0 if st.session_state.analysis_type == "Documentation" else 1
        )

        st.session_state.prompt_complexity = st.radio(
            "Prompt Complexity", 
            ["basic", "detailed", "advanced"],
            index=["basic", "detailed", "advanced"].index(st.session_state.prompt_complexity)
        )
        
        # Show selected prompts
        prompt_options = st.session_state.DOCUMENTATION_PROMPTS if st.session_state.analysis_type == "Documentation" else st.session_state.AI_DETECTION_PROMPTS
        selected_prompt = prompt_options[st.session_state.prompt_complexity]
        st.subheader("Selected Prompt:")
        st.info(selected_prompt)
    
    with tab1:  # Main analysis tab
        st.header("GitHub Code Search & Analysis")

        # Search interface
        search_query = st.text_input("Enter code search query:", 
                                placeholder="e.g., CNN implementation")
        
        # Advanced filters UI
        with st.expander("🔍 Advanced Search Filters"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                file_extension = st.text_input("File Extension", 
                                            placeholder=".py, .js, etc.")
                min_repo_size = st.number_input("Min Repository Size (KB)", 
                                            min_value=0, value=0)
                
            with col2:
                directory_path = st.text_input("Directory Path", 
                                            placeholder="/src/, /docs/")
                min_followers = st.number_input("Min User Followers", 
                                            min_value=0, value=0)
                
            with col3:
                language_filter = st.text_input("Language Filter", 
                                            placeholder="e.g., Python, Java")
                use_date_filter = st.checkbox("Filter by date?")
                last_pushed = None
                default_date = datetime.date(2020, 1, 1)
                if use_date_filter:
                    last_pushed = st.date_input("Last Pushed After", value=default_date)

        # Construct quality filters
        QUALITY_FILTERS = []
        if file_extension:
            QUALITY_FILTERS.append(f"extension:{file_extension}")
        if directory_path:
            QUALITY_FILTERS.append(f"path:{directory_path}")
        if min_repo_size > 0:
            QUALITY_FILTERS.append(f"repo:>={min_repo_size}")
        if min_followers > 0:
            QUALITY_FILTERS.append(f"user:>={min_followers} followers")
        if last_pushed:
            QUALITY_FILTERS.append(f"pushed:>={last_pushed.strftime('%Y-%m-%d')}")
        if language_filter:
            QUALITY_FILTERS.append(f"language:{language_filter}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_mode = st.selectbox("Select Analysis Mode:", 
                                       ["Documentation Generator", "AI Code Detection"])
        
        with col2:
            prompt_level = st.selectbox("Prompt Complexity:", 
                                      ["basic", "detailed", "advanced"])
        
        if st.button("Analyze Code"):
            if not search_query:
                st.warning("Please enter a search query")
                return
            else:
                enhanced_query = f"{search_query} {' '.join(QUALITY_FILTERS)}"
                st.write(f"Enhanced Query: {enhanced_query}")
            
            # Select prompt based on analysis mode and complexity
            if analysis_mode == "Documentation Generator":
                prompt = st.session_state.DOCUMENTATION_PROMPTS.get(prompt_level, st.session_state.DOCUMENTATION_PROMPTS["detailed"])
            else:  # AI Code Detection
                prompt = st.session_state.AI_DETECTION_PROMPTS.get(prompt_level, st.session_state.AI_DETECTION_PROMPTS["detailed"])
            
            with st.spinner("Searching GitHub and analyzing code..."):
                # GitHub Code Search
                search_results = search_github_code(enhanced_query)
                print(search_results)
                
                if search_results and "items" in search_results:
                    st.success(f"Found {search_results['total_count']} results")
                    
                    # Process first 3 results for demonstration
                    for item in search_results["items"][:3]:
                        with st.expander(f"File: {item['name']} (Repo: {item['repository']['full_name']})"):
                            # Get raw code content
                            raw_url = item["html_url"].replace(
                                "https://github.com", 
                                "https://raw.githubusercontent.com").replace("/blob", "")
                            
                            code_response = requests.get(raw_url)
                            
                            if code_response.status_code == 200:
                                code_snippet = code_response.text[:2500]  # Increased limit for better analysis
                                # Create two tabs for separating GitHub Response and LLM Analysis
                                tab_github, tab_analysis = st.tabs(["📂 GitHub Code Retrieved", "🤖 LLM Analysis"])
                    
                                with tab_github:
                                    st.subheader(f"File: {item['name']} (Repo: {item['repository']['full_name']})")
                                    st.code(code_snippet, language='python')

                                with tab_analysis:
                                    with st.spinner("Analyzing code with LLM..."):
                                        analysis = analyze_with_llm(code_snippet, prompt)
                                        
                                        if analysis:
                                            st.write(analysis)
                                        else:
                                            st.error("Failed to analyze code.")
                            else:
                                st.error("Failed to retrieve code content")
                else:
                    st.error("No results found or error in search")

if __name__ == "__main__":
    main()