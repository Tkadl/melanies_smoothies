# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col

# 🧾 Add a name box for the customer
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# 🍓 App title and description
st.title(':cup_with_straw: Customize Your Smoothie!:cup_with_straw:')
st.write("Choose the fruits you want in your custom Smoothie!")

# 🔌 Connect to Snowflake and pull fruit options
conn = st.experimental_connection('snowflake')
df = conn.query('SELECT FRUIT_NAME FROM smoothies.public.fruit_options')

# 🧺 Let user select fruits
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    df["FRUIT_NAME"].tolist(),
    max_selections=5
)

# 🍹 Process selected ingredients
if ingredients_list:
    ingredients_string = ''
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

    # 🖱️ Submit button logic
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        insert_sql = f"INSERT INTO smoothies.public.orders(ingredients, name_on_order) VALUES ('{ingredients_string}', '{name_on_order}')"
        conn.query(insert_sql)
        st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
