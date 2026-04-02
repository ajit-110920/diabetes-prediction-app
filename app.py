import streamlit as st
import pickle
import pandas as pd
import mysql.connector

# -------------------------------
# LOAD MODEL & SCALER
# -------------------------------
model = pickle.load(open("modelForPrediction.pickle", 'rb'))
scaler = pickle.load(open("standardScalar.pickle", 'rb'))

# -------------------------------
# DATABASE CONNECTION
# -------------------------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="yourpassword",   # 🔴 CHANGE THIS
        database="diabetes_db"
    )

# -------------------------------
# CREATE TABLE
# -------------------------------
def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INT AUTO_INCREMENT PRIMARY KEY,
        pregnancies INT,
        glucose INT,
        blood_pressure INT,
        skin_thickness INT,
        insulin INT,
        bmi FLOAT,
        dpf FLOAT,
        age INT,
        prediction INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()

# -------------------------------
# SAFE TYPE CONVERSION FUNCTION
# -------------------------------
def convert_types(data, prediction):
    clean_data = [
        int(data[0]),
        int(data[1]),
        int(data[2]),
        int(data[3]),
        int(data[4]),
        float(data[5]),
        float(data[6]),
        int(data[7])
    ]
    return clean_data, int(prediction)

# -------------------------------
# INSERT DATA
# -------------------------------
def save_to_db(data, prediction):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        clean_data, prediction = convert_types(data, prediction)

        query = """
        INSERT INTO records 
        (pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, dpf, age, prediction)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(query, (*clean_data, prediction))
        conn.commit()

    except Exception as e:
        st.error(f"Database Error: {e}")

    finally:
        cursor.close()
        conn.close()

# -------------------------------
# FETCH HISTORY
# -------------------------------
def fetch_data():
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM records ORDER BY created_at DESC", conn)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# -------------------------------
# MAIN APP
# -------------------------------
def main():
    st.title("🩺 Diabetes Prediction Application")
    st.markdown("#### 📊 Check Your Diabetes Report")
    st.image("diabet.jpg")

    create_table()

    # Sidebar Navigation
    menu = ["Prediction", "History"]
    choice = st.sidebar.selectbox("Navigation", menu)

    # -------------------------------
    # PREDICTION PAGE
    # -------------------------------
    if choice == "Prediction":

        with st.form("diabetes_form"):
            st.subheader("Enter your health details")

            pregnancies = st.number_input("Pregnancies", 0, 20, step=1)
            glucose = st.number_input("Glucose Level (mg/dL)", 0, 300, step=1)
            blood_pressure = st.number_input("Blood Pressure (mm Hg)", 0, 200, step=1)
            skin_thickness = st.number_input("Skin Thickness (mm)", 0, 100, step=1)
            insulin = st.number_input("Insulin Level (μU/mL)", 0, 900, step=1)
            bmi = st.number_input("BMI", 0.0, 70.0, step=0.1)
            dpf = st.number_input("Diabetes Pedigree Function", 0.0, 2.5, step=0.01)
            age = st.number_input("Age", 10, 120, step=1)

            submitted = st.form_submit_button("Predict")

        if submitted:
            try:
                input_data = pd.DataFrame([[pregnancies, glucose, blood_pressure,
                                            skin_thickness, insulin, bmi, dpf, age]],
                                          columns=['Pregnancies', 'Glucose', 'BloodPressure',
                                                   'SkinThickness', 'Insulin', 'BMI',
                                                   'DiabetesPedigreeFunction', 'Age'])

                # Scale input
                standardized_data = scaler.transform(input_data)

                # Predict
                prediction = model.predict(standardized_data)[0]

                # Save to DB
                input_values = [
                    pregnancies, glucose, blood_pressure,
                    skin_thickness, insulin, bmi, dpf, age
                ]

                save_to_db(input_values, prediction)

                # Show result
                if int(prediction) == 1:
                    st.error("⚠️ Diabetes Result: POSITIVE")
                    st.markdown("### Recommended Precautions:")
                    st.write("• Monitor blood glucose regularly")
                    st.write("• Take prescribed medication")
                    st.write("• Stay hydrated")
                    st.write("• Manage stress")
                    st.write("• Follow diabetic diet")
                else:
                    st.success("✅ Diabetes Result: NEGATIVE")

                st.balloons()

            except Exception as e:
                st.error(f"Prediction Error: {e}")

    # -------------------------------
    # HISTORY PAGE
    # -------------------------------
    elif choice == "History":
        st.subheader("📜 Prediction History")

        df = fetch_data()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No records found.")


# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    main()