# Import python packages
import streamlit as st
import snowflake.connector
from snowflake.connector.pandas_tools import pd_writer
import requests

# 🧾 Add a name box for the customer
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# 🍓 App title and description
st.title(':cup_with_straw: Customize Your Smoothie!:cup_with_straw:')
st.write("Choose the fruits you want in your custom Smoothie!")

# 🔌 Connect to Snowflake directly
try:
    # Get connection parameters from secrets
    conn = snowflake.connector.connect(
        user=st.secrets["connections"]["snowflake"]["user"],
        password=st.secrets["connections"]["snowflake"]["password"],
        account=st.secrets["connections"]["snowflake"]["account"],
        warehouse=st.secrets["connections"]["snowflake"]["warehouse"],
        database=st.secrets["connections"]["snowflake"]["database"],
        schema=st.secrets["connections"]["snowflake"]["schema"]
    )
    
    # Create a cursor object
    cursor = conn.cursor()
    
    # Execute a query to fetch fruit options
    cursor.execute("SELECT FRUIT_NAME FROM smoothies.public.fruit_options")
    
    # Fetch all the results
    result = cursor.fetchall()
    
    # Extract fruit names from the result
    fruit_options = [row[0] for row in result]
    
    # 🧺 Let user select fruits
    ingredients_list = st.multiselect(
        'Choose up to 5 ingredients:',
        fruit_options,
        max_selections=5
    )
    
    # 🍹 Process selected ingredients
    if ingredients_list:
        ingredients_string = ''
        
        for fruit_chosen in ingredients_list:
            ingredients_string += fruit_chosen + ' '
            smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{fruit_chosen.lower()}")
            sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
    
        # 🖱️ Submit button logic
        time_to_insert = st.button('Submit Order')
        if time_to_insert:
            # Execute SQL to insert the order
            insert_query = f"INSERT INTO smoothies.public.orders(ingredients, name_on_order) VALUES ('{ingredients_string}', '{name_on_order}')"
            cursor.execute(insert_query)
            conn.commit()
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")

except Exception as e:
    st.error(f"An error occurred: {e}")
    st.error("Please check your Snowflake connection parameters in the secrets.")

finally:
    # Close cursor and connection
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
