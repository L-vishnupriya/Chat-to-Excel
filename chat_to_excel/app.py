import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import google.generativeai as genai

# Configure Gemini API directly
genai.configure(api_key="AIzaSyCoa_o0WM6Y_Bt3LTd76kklfIAjHsgiTIs")

st.set_page_config(page_title="Chat to SQL Analyst", layout="wide")
st.title("Chat to Excel")
st.write("Upload a CSV or Excel file, ask questions in English, and get SQL-powered answers.")

uploaded_file = st.file_uploader("Upload a .csv or .xlsx file", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    st.write("###  Uploaded Data")
    st.dataframe(df)

    # Save DataFrame to in-memory SQLite
    conn = sqlite3.connect(":memory:")
    df.to_sql("data", conn, index=False, if_exists="replace")

    user_query = st.text_input(" Ask a question (we'll turn it into SQL)")

    if user_query:
        prompt = f"""
        You are an expert data analyst. Convert the user's question into an SQL query.
        The table name is `data`.

        Question: {user_query}

        Data Preview:
        {df.head(3).to_string(index=False)}

        SQL Query:
        """

        with st.spinner(" converting to SQL..."):
            try:
                model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
                response = model.generate_content(prompt)
                sql_query = response.text.strip().strip("```sql").strip("```")
                st.code(sql_query, language="sql")
            except Exception as e:
                st.error(f"Gemini Error: {e}")
                st.stop()

        # Run SQL query on SQLite
        try:
            result = pd.read_sql_query(sql_query, conn)

            output_type = st.radio(" Select output format:", ["Table", "Chart"], horizontal=True)

            if output_type == "Table":
                st.dataframe(result)
                csv = result.to_csv(index=False).encode("utf-8")
                st.download_button("⬇ Download result as CSV", csv, "result.csv", "text/csv")

            elif output_type == "Chart":
                if result.shape[1] == 2:
                    x_col, y_col = result.columns[0], result.columns[1]
                    chart_type = st.selectbox("Select chart type:", ["Bar", "Line", "Pie"])

                    if chart_type == "Bar":
                        st.bar_chart(result.set_index(x_col))
                    elif chart_type == "Line":
                        st.line_chart(result.set_index(x_col))
                    elif chart_type == "Pie":
                        fig, ax = plt.subplots()
                        ax.pie(result[y_col], labels=result[x_col], autopct='%1.1f%%')
                        ax.axis("equal")
                        st.pyplot(fig)
                else:
                    st.warning("Chart view supports only 2-column results.")
        except Exception as e:
            st.error(f" SQL execution error: {e}")
