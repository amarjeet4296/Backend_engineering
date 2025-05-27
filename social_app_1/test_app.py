import streamlit as st

st.title("Simple Test App")
st.write("If you can see this, Streamlit is working correctly!")

# Add a simple widget
number = st.slider("Select a number", 0, 100, 50)
st.write(f"You selected: {number}")
