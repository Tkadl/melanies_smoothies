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
    
    # Execute a query to fetch fruit options and their search terms
    cursor.execute("SELECT FRUIT_NAME, SEARCH_ON FROM smoothies.public.fruit_options")
    
    # Fetch all the results
    result = cursor.fetchall()
    
    # Create a dictionary to map fruit names to their search terms
    fruit_to_search_term = {}
    # Extract fruit names for the multiselect
    fruit_options = []
    
    for row in result:
        fruit_name = row[0]
        search_term = row[1] if row[1] else row[0]  # Use SEARCH_ON if available, otherwise use FRUIT_NAME
        fruit_options.append(fruit_name)
        fruit_to_search_term[fruit_name] = search_term
    
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
            
            # Use the search term from our mapping dictionary
            search_term = fruit_to_search_term.get(fruit_chosen, fruit_chosen.lower())
            
            # Format the search term for the API call
            formatted_search_term = search_term.lower().replace(' ', '')
            
            # Display fruit nutrition information
            st.subheader(f"{fruit_chosen} Nutrition Information")
            
            try:
                # Try to get data from the API using the search term
                smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{formatted_search_term}")
                
                # Check if the request was successful
                if smoothiefroot_response.status_code == 200:
                    sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
                else:
                    st.warning(f"Could not retrieve nutrition data for {fruit_chosen}. Status code: {smoothiefroot_response.status_code}")
                    
                    # Try the "all" endpoint as a fallback
                    st.write("Checking the comprehensive fruit database...")
                    all_fruits_response = requests.get("https://my.smoothiefroot.com/api/fruit/all")
                    
                    if all_fruits_response.status_code == 200:
                        all_fruits_data = all_fruits_response.json()
                        
                        # Search for the fruit in the all fruits data
                        found_data = None
                        search_variations = [search_term.lower(), fruit_chosen.lower()]
                        
                        for item in all_fruits_data:
                            if 'name' in item and item['name'].lower() in search_variations:
                                found_data = [item]
                                break
                        
                        if found_data:
                            st.success(f"Found nutrition data for {fruit_chosen} in the comprehensive database!")
                            sf_df = st.dataframe(data=found_data, use_container_width=True)
                        else:
                            st.error(f"Could not find nutrition data for {fruit_chosen} in any database.")
                    else:
                        st.error("Could not access the comprehensive fruit database.")
                
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
