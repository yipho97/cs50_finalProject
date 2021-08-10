# My Health App
#### **Video Demo**:  <https://youtu.be/Cg0Etbru33Y>
#### **Description**:
MyHealthApp made with diet & calories API, running on Flask web framework with vanilla HTML/CSS/JS. 

**Aim**: 
Allow users to keep track of daily caloric intake as well as food nutritional information through the use of open-source API.

**Environment setup**:\
`pip install -r requirements.txt`\
`cd cs50_finalProject`\
`flask run`

**Accessing Sqlite DB**\
`sqlite3 test.db`

**`app.py`**:
- Flask session is used to track user_id to insert personalized data into db.

- Login is required to access "/", "/diet", "/macros" route as existing data is required.

- login function routes to "/login" when user is not logged in and attempts to access @login_required pages. Form POSTED to this endpoitn will be checked against db to allow/deny user access.

- register function routes to "/register" which also accepts a form via POST to be logged into db.

- index function routes to "/" which displays user's profile and caloric goals, if not set, return blank profile. It also accepts a POSTED form to update user's profile/caloric goals on db.

- logout function routes to "/logout" which clears the user's session/log out and redirects to login page

- search function routes to "/search" which accepts query string from the url via a GET request. Calorie API is called with query string to return nutritional information as response.

- diet function routes to "/diet" which queries db for existing diet entries for the day. It also accepts a POSTED form from users to insert nutritional information of their entry after passing their entry to the calorie API and inserting the reponse into the db.

- macros function routes to "/macros" which queries fitness calculator API to get the different types of diet suitable for user based on their profile as response.

#### **`root.html`**
Outline of the website to be inherited by future templates
- navbar
- searchbar
- display container

#### **`index.html`**
Displays users info 

#### **`login.html`**
Form for login/registration

#### **`diet.html`**
- Form for adding diet intake
- Date selector for querying diet for specific day
- Table displaying daily diet with remaining counts and green/red indicator for macros within/exceeded goal.

#### **`macros.html`**
- Form for users to edit/update their profile
- Hidden form after first form has been submitted with "Search" button for users to update their macro goals.

#### **`search.html`**
- Form to receive query from user and display nutritional value in list.

#### **`helpers.py`**
Login required logic to check if user's session key is found, if not redirect to    "/login" route to log in.

#### **`test.db`**
Sqlite3 database with 
- users
- profile
- entries
- diet
- diet_goal