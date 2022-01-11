import streamlit as st
from pages import health, sport

"""
[![Github](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Lucasblld)
&nbsp[![Linkedin](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/lucas-billaud/)
"""

PAGES = {
    "Health": health,
    "Sport": sport
}
st.sidebar.title('Navigation')
selection = st.sidebar.selectbox("Go to", list(PAGES.keys()))
page = PAGES[selection]
page.app()