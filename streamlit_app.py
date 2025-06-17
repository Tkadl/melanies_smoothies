# Import python packages
import streamlit as st
import snowflake.connector
from snowflake.connector.pandas_tools import pd_writer
import requests
import pandas as pd
from snowflake.snowpark.functions import col

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
    
    # Get Snowpark session
    session = conn.cursor().connection._session
    
    # Execute a query to fetch fruit options with SEARCH_ON column
    my_dataframe = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"), col("SEARCH_ON"))
    
    # Convert Snowpark DataFrame to Pandas DataFrame
    pd_df = my_dataframe.to_pandas()
    
    # Display the dataframe (for debugging, can be commented out later)
    st.dataframe(pd_df)
    st.stop()  # This will stop execution here for debugging
    
    # 🧺 Let user select fruits
    ingredients_list = st.multiselect(
        'Choose up to 5 ingredients:',
        my_dataframe,  # Use my_dataframe for selection
        max_selections=5
    )
    
    # 🍹 Process selected ingredients
    if ingredients_list:
        ingredients_string = ''
        
        for fruit_chosen in ingredients_list:
            ingredients_string += fruit_chosen + ' '
            
            # Get the SEARCH_ON value for the selected fruit
            search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
            st.write(f'The search value for {fruit_chosen} is {search_on}.')
            
            # Display fruit nutrition information
            st.subheader(f"{fruit_chosen} Nutrition Information")
            
            try:
                # Use search_on instead of fruit_chosen for API call
                fruityvice_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
                
                # Check if the request was successful
                if fruityvice_response.status_code == 200:
                    sf_df = st.dataframe(data=fruityvice_response.json(), use_container_width=True)
                else:
                    st.warning(f"Could not retrieve nutrition data for {fruit_chosen}. Status code: {fruityvice_response.status_code}")
            except Exception as e:
                st.error(f"Error retrieving nutrition data for {fruit_chosen}: {e}")
    
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
