# Import python packages
import streamlit as st
import snowflake.connector
import requests
import pandas as pd

# 🧾 Add a name box for the customer
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# 🍓 App title and description
st.title(':cup_with_straw: Customize Your Smoothie!:cup_with_straw:')
st.write("Choose the fruits you want in your custom Smoothie!")

# Function to find fruit in the complete fruit data
def find_fruit_in_all_data(all_data, search_term):
    search_term_lower = search_term.lower()
    for fruit in all_data:
        if 'name' in fruit and fruit['name'].lower() == search_term_lower:
            return fruit
    return None

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
    
    # Execute a query to fetch fruit options with SEARCH_ON column
    cursor.execute("SELECT FRUIT_NAME, SEARCH_ON FROM smoothies.public.fruit_options")
    
    # Fetch all the results
    result = cursor.fetchall()
    
    # Create a pandas DataFrame from the results
    pd_df = pd.DataFrame(result, columns=['FRUIT_NAME', 'SEARCH_ON'])
    
    # Fetch all fruits data from the API once
    try:
        all_fruits_response = requests.get("https://my.smoothiefroot.com/api/fruit/all")
        if all_fruits_response.status_code == 200:
            all_fruits_data = all_fruits_response.json()
        else:
            all_fruits_data = []
            st.warning("Could not fetch the complete fruits database. Some nutrition information may not be available.")
    except Exception as e:
        all_fruits_data = []
        st.warning(f"Error fetching complete fruits database: {e}")
    
    # 🧺 Let user select fruits
    ingredients_list = st.multiselect(
        'Choose up to 5 ingredients:',
        pd_df['FRUIT_NAME'].tolist(),  # Use the FRUIT_NAME column for selection
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
                # First try using the direct API endpoint with the search_on value
                formatted_search = search_on.lower().replace(' ', '')
                direct_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{formatted_search}")
                
                # If direct API call fails, search in the all_fruits_data
                if direct_response.status_code == 200:
                    st.dataframe(data=direct_response.json(), use_container_width=True)
                else:
                    # Search in the all_fruits_data
                    if all_fruits_data:
                        # Try with the search_on value first
                        fruit_data = find_fruit_in_all_data(all_fruits_data, search_on)
                        
                        # If not found with search_on, try with original fruit_chosen
                        if not fruit_data and search_on != fruit_chosen:
                            fruit_data = find_fruit_in_all_data(all_fruits_data, fruit_chosen)
                        
                        # If found, display the data
                        if fruit_data:
                            st.success(f"Found nutrition data for {fruit_chosen} in the comprehensive database!")
                            st.dataframe(data=[fruit_data], use_container_width=True)
                        else:
                            st.error(f"Could not find nutrition data for {fruit_chosen} in any database.")
                    else:
                        st.error(f"Could not retrieve nutrition data for {fruit_chosen}.")
                
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
