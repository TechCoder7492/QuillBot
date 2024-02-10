import streamlit as st
from openai import OpenAI
import langchain
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import streamlit_authenticator as stauth
import pickle
from pathlib import Path
import yaml
from yaml.loader import SafeLoader

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

#---- user authentication -------
hashed_passwords = stauth.Hasher(['au1234', 'au12345','au123456']).generate()
with open (Path(__file__).parent/"config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

def logout():
    authenticator._implement_logout()
def feedback_button():
        google_forms_url = "https://forms.gle/Vx9X4jUhek2wdYwA9"
        webbrowser.open_new_tab(google_forms_url)

name,authentication_status,username = authenticator.login("main")
if authentication_status == False:
    st.error("username/password entered is wrong")
if authentication_status == None:
    st.error("please enter the valid details")
if authentication_status:
    embeddings = OpenAIEmbeddings()

    client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))

    subject_paths = {
        'Python': './data/python',
        'Software Engineering': './data/se',
        'Cryptography and inforrmation security': './data/cis',
        'Java': './data/java',
        'Cloud omputing': './data/fcc'
    }

    def get_completion(prompt, model="gpt-3.5-turbo-0613"):
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
            )
        return response.choices[0].message.content

    marks_relevance = {
        2: 2,
        5: 4,
        10: 5
    }


    with st.sidebar:
        st.button("Logout",on_click=logout)
        st.title("Quill Bot")
        subject_choice = st.selectbox(label="Subject", options=subject_paths.keys(), placeholder="Subject")
        marks_choice = st.selectbox(label="Marks", options=marks_relevance.keys())
        st.button("Submit Feedback",on_click=feedback_button)


     # Using st.form to create a form
    with st.form(key='question_form'):
        question_input = st.text_input("Your Question", key='question_input')

        # Adding a submit button to the form
        submit_button = st.form_submit_button(label='Submit')

    # Processing the form data only if the submit button is clicked
    if submit_button:
        st.chat_message("human").write(question_input)

        new_db = Chroma(persist_directory=subject_paths[subject_choice], embedding_function=embeddings)

        result = new_db.similarity_search(question_input, marks_relevance[marks_choice])
        prompt = f"""
        You are an AI assistant that helps the students to get the answers to their questions based on the textbook knowledge that you are\
        provided with.\
        your task is to provide the answer in a student-friendly manner but you should not alter the data in the response and make sure all the data is covered thoroughly\
        add any relevant data to the response which can be helpful to the user\
        marks are delimited by ```,
        if it is for 2 marks then make sure that the response has at least 100 words with no plagiarism\
        if it is for 5 marks then make sure that the response has at least 300 words with no plagiarism\
        if it is for 10 marks then make sure that the response has at least 500 words with no plagiarism\
        if the response is smaller then add extra data from our knowledge\
        provide a real life example as a code snippet for better experience if the answer is related to programming\
        if at any case the answer is not related to the question delimeted in by ` then give a answer of your own and tell the user it is not found in the textbook\
        given the response generated by the LLM is delimited by ```,
        response:```{result}```
        marks:``{marks_relevance[marks_choice]}``
        question:`{question_input}`
        """
        response = get_completion(prompt)

        st.chat_message("AI").write(str(response))
    
        
