"""
Enhanced AI Workflow for Government Social Security Department
Main application file integrating all components into a unified system.
"""

import streamlit as st
import pandas as pd
import asyncio
import tempfile
import os
import logging
import json
from datetime import datetime
import time

# Import database connector
from data.db_connector import DatabaseConnector

# Import agents
from agents.simple_orchestrator import SimpleOrchestratorAgent

# Import existing agents for reference if needed
from data_collector import DataCollector
from validator import ValidatorAgent
from assessor import AssessorAgent
from counselor import CounselorAgent

# Import utilities
from utils.reasoning import ReActReasoning
from utils.observability import ObservabilityTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="AI-Powered Social Security Application System",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state variables
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

if 'db' not in st.session_state:
    st.session_state.db = None

if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Home"
    
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
    
if 'current_result' not in st.session_state:
    st.session_state.current_result = {}

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'upload_files' not in st.session_state:
    st.session_state.upload_files = []

# Function to initialize components
def initialize_components():
    try:
        # Initialize database connector
        st.session_state.db = DatabaseConnector()
        
        # Initialize simple orchestrator agent
        st.session_state.orchestrator = SimpleOrchestratorAgent()
        
        # Mark as initialized
        st.session_state.initialized = True
        
        logger.info("All components initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        return False

# Initialize components if not already done
if not st.session_state.initialized:
    with st.spinner("Initializing AI components..."):
        success = initialize_components()
        if not success:
            st.error("Failed to initialize application components. Please check the logs.")

# Title and application description
st.title("🤖 AI-Powered Social Security Application System")

# Create sidebar for navigation
with st.sidebar:
    st.header("Navigation")
    
    # Create tabs
    tabs = [
        "Home", 
        "New Application", 
        "Application Status", 
        "Guidance Chat", 
        "Analytics", 
        "System Info"
    ]
    
    selected_tab = st.radio("Select a page", tabs, index=tabs.index(st.session_state.current_tab))
    st.session_state.current_tab = selected_tab
    
    # Show system status
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Status")
    
    if st.session_state.initialized:
        st.sidebar.success("✅ System Ready")
    else:
        st.sidebar.error("❌ System Not Initialized")

# Home Tab
if selected_tab == "Home":
    st.header("🏠 Welcome to the Social Security Application System")
    
    st.markdown("""
    This AI-powered system helps process social security applications efficiently and fairly.
    
    ### Key Features:
    
    1. **Automated Document Processing**: Extracts information from various document types
    2. **Advanced Data Validation**: Ensures data quality and consistency
    3. **ML-Based Eligibility Assessment**: Fair and consistent assessment of applications
    4. **Economic Enablement Recommendations**: Personalized guidance for applicants
    5. **Interactive Chat Assistance**: Get answers to your questions
    
    ### Getting Started:
    
    - Use the **New Application** tab to submit a new application
    - Check the status of existing applications in the **Application Status** tab
    - Get assistance and guidance in the **Guidance Chat** tab
    - View insights and analytics in the **Analytics** tab
    """)
    
    # Quick access buttons
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 New Application", use_container_width=True):
            st.session_state.current_tab = "New Application"
            st.experimental_rerun()
    
    with col2:
        if st.button("🔍 Check Status", use_container_width=True):
            st.session_state.current_tab = "Application Status"
            st.experimental_rerun()
    
    with col3:
        if st.button("💬 Get Assistance", use_container_width=True):
            st.session_state.current_tab = "Guidance Chat"
            st.experimental_rerun()

# New Application Tab
elif selected_tab == "New Application":
    st.header("📝 New Application Submission")
    
    # Application form
    with st.expander("📋 Application Details", expanded=True):
        st.subheader("Personal Information")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            dob = st.date_input("Date of Birth")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
        with col2:
            nationality = st.text_input("Nationality")
            email = st.text_input("Email Address")
            phone = st.text_input("Phone Number")
        
        st.subheader("Financial Information")
        
        col1, col2 = st.columns(2)
        with col1:
            income = st.number_input("Annual Income (AED)", min_value=0)
            assets = st.number_input("Total Assets (AED)", min_value=0)
        
        with col2:
            family_size = st.number_input("Family Size", min_value=1, max_value=20)
            liabilities = st.number_input("Total Liabilities (AED)", min_value=0)
        
        employment_status = st.selectbox(
            "Employment Status", 
            ["Employed", "Self-employed", "Unemployed", "Retired", "Student", "Other"]
        )
        
        address = st.text_area("Residential Address")
    
    # Document upload section
    with st.expander("📤 Document Upload", expanded=True):
        st.markdown("""
        Please upload the following required documents:
        - Proof of identity (Emirates ID, passport)
        - Proof of income (salary certificate, bank statements)
        - Proof of address (utility bill, rental agreement)
        - Family documents (if applicable)
        """)
        
        uploaded_files = st.file_uploader(
            "Upload Documents", 
            type=['pdf', 'png', 'jpg', 'jpeg', 'xlsx', 'xls', 'csv'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.session_state.upload_files = uploaded_files
            
            # Display uploaded files
            st.subheader("Uploaded Documents")
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.size} bytes)")
    
    # Submit button
    if st.button("Submit Application", type="primary"):
        if not uploaded_files:
            st.error("Please upload at least one supporting document")
        elif not name or not address or income <= 0 or family_size <= 0:
            st.error("Please fill in all required fields")
        else:
            with st.spinner("Processing application..."):
                # Create progress bar
                progress_bar = st.progress(0)
                status_area = st.empty()
                
                try:
                    # Step 1: Process each document
                    status_area.info("🔍 Processing documents...")
                    progress_bar.progress(10)
                    
                    # Initialize results dictionary
                    results = {
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "income": income,
                        "family_size": family_size,
                        "address": address,
                        "assets": assets,
                        "liabilities": liabilities,
                        "employment_status": employment_status,
                        "demographic_info": {
                            "gender": gender,
                            "nationality": nationality,
                            "date_of_birth": dob.strftime("%Y-%m-%d")
                        },
                        "validation_status": "",
                        "assessment_status": "",
                        "risk_level": ""
                    }
                    
                    # Process first document for detailed extraction
                    if uploaded_files:
                        first_file = uploaded_files[0]
                        
                        # Save file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{first_file.name.split('.')[-1]}") as tmp_file:
                            tmp_file.write(first_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        # Process the document
                        status_area.info(f"🔍 Extracting information from {first_file.name}...")
                        
                        # Use the integrated orchestrator for document processing
                        document_bytes = first_file.getvalue()
                        doc_result = asyncio.run(st.session_state.orchestrator.process_application(
                            document_bytes,
                            first_file.name
                        ))
                        
                        # Extract the results from the orchestrator output
                        extracted_data = doc_result.get('extracted_data', {})
                        
                        # Update results with extracted information if available
                        for key in ['income', 'family_size', 'address']:
                            if key in extracted_data and extracted_data[key] and results[key] == 0:
                                results[key] = extracted_data[key]
                        
                        # Update validation and eligibility information
                        if 'validation_results' in doc_result:
                            results['validation_status'] = 'valid' if doc_result['validation_results'].get('is_valid', False) else 'invalid'
                            
                        if 'eligibility_results' in doc_result:
                            results['assessment_status'] = 'approved' if doc_result['eligibility_results'].get('is_eligible', False) else 'rejected'
                            results['risk_level'] = doc_result['eligibility_results'].get('details', {}).get('risk_level', 'medium')
                        
                        # Clean up temporary file
                        os.unlink(tmp_path)
                    
                    progress_bar.progress(30)
                    
                    # Step 2: Validate the application
                    status_area.info("✅ Validating application data...")
                    
                    validation_agent = DataValidationAgent()
                    is_valid, validation_errors = validation_agent.validate(results)
                    
                    results['validation_status'] = "✅ Valid" if is_valid else "❌ Invalid"
                    
                    if not is_valid:
                        status_area.warning("Validation failed with the following errors:")
                        for error in validation_errors:
                            st.error(error)
                    
                    progress_bar.progress(50)
                    
                    # Step 3: Assess eligibility
                    status_area.info("🧮 Assessing eligibility...")
                    
                    eligibility_agent = EligibilityAgent()
                    is_eligible, reasons, assessment_details = eligibility_agent.assess_application(results)
                    
                    results['assessment_status'] = "✅ Approved" if is_eligible else "❌ Rejected"
                    results['risk_level'] = assessment_details['risk_level']
                    results['eligibility_score'] = assessment_details.get('ml_eligibility_score', 0.0)
                    results['enablement_recommendations'] = assessment_details.get('enablement_recommendations', [])
                    
                    progress_bar.progress(70)
                    
                    # Step 4: Generate recommendations
                    status_area.info("💡 Generating recommendations...")
                    
                    counselor_agent = EnhancedCounselorAgent()
                    recommendations = counselor_agent.generate_recommendations(results)
                    explanation = counselor_agent.explain_decision(results)
                    
                    results['recommendations'] = recommendations
                    results['explanation'] = explanation
                    
                    progress_bar.progress(90)
                    
                    # Step 5: Store in database
                    status_area.info("💾 Storing application data...")
                    
                    # Store application in database
                    if st.session_state.db:
                        app_id = st.session_state.db.store_application(results)
                        results['id'] = app_id
                    
                    progress_bar.progress(100)
                    
                    # Store result in session state
                    st.session_state.current_result = results
                    st.session_state.processing_complete = True
                    
                    # Success message
                    status_area.success("✅ Application processed successfully!")
                    
                    # Show results
                    st.subheader("Application Results")
                    
                    if is_eligible:
                        st.success(f"✅ Application approved with {assessment_details['risk_level']} risk level")
                    else:
                        st.warning(f"❌ Application not approved. Reason(s):")
                        for reason in reasons:
                            st.error(reason)
                    
                    # Display more details
                    st.json(json.dumps({
                        "status": results['assessment_status'],
                        "risk_level": results['risk_level'],
                        "eligibility_score": results.get('eligibility_score', 0),
                        "income_per_member": income / family_size if family_size > 0 else 0,
                        "application_id": results.get('id', 'Not stored')
                    }))
                    
                    # Show recommendations
                    st.subheader("Recommendations")
                    for rec in recommendations:
                        with st.expander(f"{rec['category']} ({rec['priority']} priority)"):
                            st.write(rec['recommendation'])
                            st.write("**Actions:**")
                            for action in rec['action_items']:
                                st.write(f"- {action}")
                
                except Exception as e:
                    logger.error(f"Error processing application: {str(e)}")
                    st.error(f"An error occurred while processing the application: {str(e)}")

# Application Status Tab
elif selected_tab == "Application Status":
    st.header("🔍 Application Status")
    
    # Search options
    search_options = st.radio(
        "Search by:",
        ["Recent Applications", "Application ID", "Applicant Name"]
    )
    
    if search_options == "Recent Applications":
        if st.session_state.db:
            # Get recent applications
            recent_apps = st.session_state.db.get_recent_applications(limit=10)
            
            if recent_apps:
                st.subheader(f"Recent Applications ({len(recent_apps)})")
                
                # Convert to DataFrame for display
                df = pd.DataFrame(recent_apps)
                
                # Format DataFrame
                if 'created_at' in df.columns:
                    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                
                # Display applications
                st.dataframe(df, use_container_width=True)
                
                # Allow selection of application
                selected_app_id = st.selectbox(
                    "Select an application to view details:",
                    options=[app['id'] for app in recent_apps],
                    format_func=lambda x: f"Application #{x} - {next((app['filename'] for app in recent_apps if app['id'] == x), '')}"
                )
                
                if selected_app_id:
                    # Get full application details
                    app_details = st.session_state.db.get_application(selected_app_id)
                    
                    if app_details:
                        st.subheader(f"Application #{selected_app_id} Details")
                        
                        # Process the application
                        results = asyncio.run(st.session_state.orchestrator.process_application(
                            app_details['document_bytes'],
                            app_details['filename']
                        ))
                        
                        # Add missing application details from the form
                        results['extracted_data'].update({
                            'name': app_details['name'],
                            'email': app_details['email'],
                            'phone': app_details['phone'],
                            'dob': app_details['dob'],
                            'gender': app_details['gender'],
                            'nationality': app_details['nationality'],
                            'employment_status': app_details['employment_status'],
                            'assets': app_details['assets'],
                            'liabilities': app_details['liabilities']
                        })
                        
                        # Display application details
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Income", f"{app_details['income']:,.2f} AED")
                            st.metric("Family Size", app_details['family_size'])
                        
                        with col2:
                            st.metric("Risk Level", app_details['risk_level'].upper())
                            st.metric("Status", app_details['assessment_status'])
                        
                        with col3:
                            if 'assets' in app_details and app_details['assets']:
                                st.metric("Assets", f"{app_details['assets']:,.2f} AED")
                            if 'liabilities' in app_details and app_details['liabilities']:
                                st.metric("Liabilities", f"{app_details['liabilities']:,.2f} AED")
                        
                        # Show address
                        st.subheader("Address")
                        st.write(app_details['address'])
                        
                        # Show recommendations if available
                        if 'enablement_recommendations' in app_details and app_details['enablement_recommendations']:
                            st.subheader("Recommendations")
                            
                            for rec in app_details['enablement_recommendations']:
                                with st.expander(f"{rec['type']} ({rec['priority']})"):
                                    st.write(f"**{rec['title']}**")
                                    st.write(rec['description'])
                                    st.write(f"Eligibility: {rec['eligibility']}")
                                    if 'link' in rec:
                                        st.write(f"[Learn More]({rec['link']})")
                    else:
                        st.error(f"Could not retrieve details for Application #{selected_app_id}")
            else:
                st.info("No applications found in the database")
        else:
            st.error("Database connection not available")
    
    elif search_options == "Application ID":
        app_id = st.number_input("Enter Application ID", min_value=1)
        
        if st.button("Search"):
            if st.session_state.db and app_id:
                app_details = st.session_state.db.get_application(app_id)
                
                if app_details:
                    st.success(f"Found Application #{app_id}")
                    
                    # Display application details
                    st.json(app_details)
                else:
                    st.error(f"Application #{app_id} not found")
            else:
                st.error("Database connection not available or invalid ID")
    
    elif search_options == "Applicant Name":
        st.warning("Name search functionality coming soon")
        applicant_name = st.text_input("Enter Applicant Name")
        
        if st.button("Search"):
            st.info("This feature is under development")

# Guidance Chat Tab
elif selected_tab == "Guidance Chat":
    st.header("💬 AI Assistance and Guidance")
    
    # Instructions
    st.markdown("""
    Chat with our AI assistant for guidance on:
    - Application process and requirements
    - Eligibility criteria
    - Document requirements
    - Economic enablement programs
    - Next steps after application
    """)
    
    # Initialize chat history if needed
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    user_message = st.chat_input("Ask a question about your application or the process")
    
    if user_message:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_message)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                message_placeholder = st.empty()
                
                # Use counselor agent to generate response
                if st.session_state.orchestrator:
                    # Get application context if available
                    app_context = st.session_state.current_result if st.session_state.processing_complete else None
                    
                    # Generate response
                    if app_context:
                        response = st.session_state.orchestrator.chat_with_counselor(app_context, user_message)
                    else:
                        # Create a minimal context if none exists
                        minimal_context = {
                            "income": 0,
                            "family_size": 0,
                            "address": "",
                            "assessment_status": "pending"
                        }
                        response = st.session_state.orchestrator.chat_with_counselor(minimal_context, user_message)
                else:
                    # Fallback if orchestrator not available
                    counselor = EnhancedCounselorAgent()
                    response = asyncio.run(counselor.chat(user_message))
                
                # Display response with typing effect
                full_response = response
                message_placeholder.write(full_response)
        
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

# Analytics Tab
elif selected_tab == "Analytics":
    st.header("📊 Application Analytics")
    
    # Check if database is available
    if st.session_state.db:
        # Get statistics
        stats = st.session_state.db.get_application_statistics()
        
        if stats:
            # Display overview statistics
            st.subheader("Overview")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Applications", stats.get('total_applications', 0))
            
            with col2:
                approved = stats.get('status_counts', {}).get('✅ Approved', 0)
                total = stats.get('total_applications', 0)
                approval_rate = (approved / total * 100) if total > 0 else 0
                st.metric("Approval Rate", f"{approval_rate:.1f}%")
            
            with col3:
                avg_income = stats.get('avg_income', 0)
                st.metric("Average Income", f"{avg_income:,.2f} AED")
            
            # Status distribution
            st.subheader("Application Status Distribution")
            
            status_counts = stats.get('status_counts', {})
            if status_counts:
                status_df = pd.DataFrame({
                    'Status': list(status_counts.keys()),
                    'Count': list(status_counts.values())
                })
                st.bar_chart(status_df, x='Status', y='Count')
            else:
                st.info("No status data available")
            
            # Risk level distribution
            st.subheader("Risk Level Distribution")
            
            risk_counts = stats.get('risk_counts', {})
            if risk_counts:
                risk_df = pd.DataFrame({
                    'Risk Level': list(risk_counts.keys()),
                    'Count': list(risk_counts.values())
                })
                st.bar_chart(risk_df, x='Risk Level', y='Count')
            else:
                st.info("No risk level data available")
        else:
            st.info("No analytics data available yet")
    else:
        st.error("Database connection not available")

# System Info Tab
elif selected_tab == "System Info":
    st.header("ℹ️ System Architecture and Information")
    
    st.subheader("Agentic AI Architecture")
    
    st.markdown("""
    This system uses a multi-agent architecture powered by locally hosted LLMs to process applications:
    
    1. **Orchestrator Agent**: Coordinates the workflow between specialized agents
    2. **Data Extraction Agent**: Processes documents and extracts information
    3. **Data Validation Agent**: Ensures data quality and consistency
    4. **Eligibility Agent**: Assesses applications using ML models
    5. **Counselor Agent**: Provides guidance and recommendations
    
    All agents use the ReAct reasoning framework for improved decision-making.
    """)
    
    # Display system diagram
    st.image("https://mermaid.ink/img/pako:eNp1kU1vwjAMhv9KlFMr7bDDmAPqByA2aYcJTeI0Q5GWJt0KUZT8d9OWUQYa8sF-_dp-7XSgDxZpQO8W3qFw61pAVw-VoZAJLx06qK3RQH46OAv4A6tiFepSqK-4sB5KAZXoYWugEWGLNmA2DfOeO-dNK2RXcgENzNCIMCF3a9zzYGLqb_lJ9i-JB-0L5tXy_u4l1ulnsdovoig-37HjkA_JzBg1EKdKtChjYzF9tGEYxBk-JaxIGHwntDw-3Pql8SgPRZsWvSUt9lW9TjYnO7HWPzujw1BfP2SQnLMMnnPJiXKZ-7y1WrfsD9QnYz0pGtDFhIGwrwY49oyhF_qQQ0N5OaQYkP33Z2lEVgBdN9Pp4pRKY1SvUEvNmH2Vjdw-1CqaGXq2iKEYJR_oqBRsGy1-AEGHDA4?type=png", caption="System Architecture")
    
    st.subheader("Technology Stack")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Core Components:**
        - Python 3.9+
        - Streamlit (UI Framework)
        - Pandas (Data Processing)
        - SQLAlchemy (Database ORM)
        - PostgreSQL (Database)
        """)
    
    with col2:
        st.markdown("""
        **AI Components:**
        - LangChain (Agent Framework)
        - LangGraph (Agent Orchestration)
        - Ollama (Local LLM Hosting)
        - ChromaDB (Vector Database)
        - Scikit-learn (ML Models)
        """)
    
    st.subheader("Model Information")
    
    # Display model information if available
    if st.session_state.orchestrator:
        st.write(f"**Primary LLM Model:** {st.session_state.orchestrator.model_name}")
        st.write("**Agent Reasoning Framework:** ReAct (Reasoning + Acting)")
        st.write("**ML Models:**")
        st.write("- Eligibility Classification: Random Forest")
        st.write("- Risk Assessment: Gradient Boosting")
    else:
        st.info("System components not fully initialized")
    
    # System status and logs
    st.subheader("System Status and Logs")
    
    if st.button("Check System Status"):
        st.write("Status checks:")
        
        # Check database connection
        if st.session_state.db:
            st.success("✅ Database connection established")
        else:
            st.error("❌ Database connection failed")
        
        # Check LLM availability
        if st.session_state.orchestrator:
            st.success("✅ LLM models available")
        else:
            st.error("❌ LLM models not initialized")
        
        # Check other components
        components = {
            "Data Extraction": DataExtractionAgent,
            "Data Validation": DataValidationAgent,
            "Eligibility Assessment": EligibilityAgent,
            "Counselor": EnhancedCounselorAgent
        }
        
        for name, component_class in components.items():
            try:
                component = component_class()
                st.success(f"✅ {name} agent available")
            except Exception as e:
                st.error(f"❌ {name} agent initialization failed: {str(e)}")

# Run the app
if __name__ == "__main__":
    # This code will be executed when the script is run directly
    pass
