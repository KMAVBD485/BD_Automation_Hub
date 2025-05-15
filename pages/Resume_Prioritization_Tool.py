import streamlit as st
import textract
import string
import pandas as pd
import nltk
import tempfile
import os
import re
from PyPDF2 import PdfReader
from docx import Document
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('stopwords')
nltk.download('punkt')

st.title(':blue[Resume Prioritization Tool] 🖍')

must_have_words_input = st.text_input('Enter must-have words (comma-separated)',  'aml, compliance, transaction, monitoring, risk, investigation, pep, sanction')
good_to_have_words_input = st.text_input('Enter good-to-have words (comma-separated)', 'kyb, kyc, due, diligence, detail-oriented, analysis, review, payment, remittance, b2c, b2b')

must_have_words = set([word.strip() for word in must_have_words_input.split(',')])
good_to_have_words = set([word.strip() for word in good_to_have_words_input.split(',')])

uploaded_files = st.file_uploader("Upload resumes", type=["pdf", "docx", "doc"], accept_multiple_files=True)

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return str(e)

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = ''
        for para in doc.paragraphs:
            text += para.text + '\n'
        return text
    except Exception as e:
        return str(e)

def extract_name_from_filename(file_name):
    name_without_extension = os.path.splitext(file_name)[0]
    name_pattern = re.compile(r'[a-zA-Z]+(?: [a-zA-Z]+)*')
    match = name_pattern.search(name_without_extension)
    if match:
        return match.group(0)
    else:
        return "Unknown"

if uploaded_files:
    fname = []
    applicant_names = []
    w1_score = []
    w2_score = []
    words = []
    alerts = []

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        applicant_name = extract_name_from_filename(file_name)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        try:
            if file_name.endswith('.pdf'):
                text = extract_text_from_pdf(temp_file_path)
            elif file_name.endswith('.docx'):
                text = extract_text_from_docx(temp_file_path)
            else:
                text = textract.process(temp_file_path).decode()

            w1 = 0
            w2 = 0
            y = text.replace('\n', '')
            y = y.translate(str.maketrans('', '', string.punctuation))
            y = y.lower()
            y = y.split()
            y_set = set(y)
            tmpstr = ""
            for word in y_set:
                if word in must_have_words:
                    w1 += 1
                    tmpstr += f"{word}, "
                if word in good_to_have_words:
                    w2 += 1
                    tmpstr += f"{word}, "

            fname.append(file_name)
            applicant_names.append(applicant_name)
            w1_score.append(w1)
            w2_score.append(w2)
            words.append(tmpstr)
            alerts.append("successfully parsed")
        except Exception as e:
            fname.append(file_name)
            applicant_names.append(applicant_name)
            w1_score.append(0)
            w2_score.append(0)
            words.append('null')
            alerts.append(f"Cannot Scan CV: {e}")
        finally:
            os.remove(temp_file_path)

    result = pd.DataFrame({
        'file name': fname,
        'applicant name': applicant_names,
        'must-have words score': w1_score,
        'good-to-have words score': w2_score,
        'total score': [(w1 * 2) + w2 for w1, w2 in zip(w1_score, w2_score)],
        'words': words,
        'alerts': alerts
    })

    result = result[['file name', 'applicant name', 'must-have words score', 'good-to-have words score', 'total score', 'words', 'alerts']]
    result = result.sort_values(by=['total score'], ascending=False)

    st.dataframe(result, hide_index=True, use_container_width=True)
