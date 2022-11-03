from fastapi import FastAPI, Depends, Body, Request, HTTPException, Path, status
from fastapi.responses import JSONResponse
import firebase_admin
from firebase_admin import db, auth
import pyrebase
import json
from jose import jwt
from pydantic import BaseModel, Json
from typing import Union, List
from fastapi.security import OAuth2PasswordBearer
'''
cred_obj = firebase_admin.credentials.Certificate('C://Users//T490s//Downloads//fastAPI//database_connect_app//mama-e0162-firebase-adminsdk-xzj4f-ea902771bc.json')
default_app = firebase_admin.initialize_app(cred_obj,{"databaseURL":"https://mama-e0162-default-rtdb.asia-southeast1.firebasedatabase.app/"}) 

ref = db.reference("/")

ref.set({
	"Books":
	{
		"Best_Sellers": -1,
        "Books_Store": -1
	}
})
ref = db.reference("/Books/Best_Sellers")
with open("C://Users//T490s//Downloads//fastAPI//database_connect_app//book_info.json", "r") as f:
	file_contents = json.load(f)

for key, value in file_contents.items():
	ref.push().set(value)
ref = db.reference("/Books/Books_Store")
ref.set(file_contents)

ref = db.reference("/Books/Books_Store")
best_sellers = ref.get()
print(best_sellers)
for key,value in best_sellers.items():
    if value["Author"] == "J.R.R. Tolkien":
        ref.child(key).set({})
		child = db.reference("Books").child("Best_Sellers").order_by_child("Price").start_at(101).get()
print(child)
ref = db.reference("/Books")
bestbooks = ref.child("Best_Sellers").get()
for key,value in bestbooks.items():
	print(value["Author"])


'''
cred_obj = firebase_admin.credentials.Certificate('C://Users//T490s//Downloads//fastAPI//database_connect_app//mama-e0162-firebase-adminsdk-xzj4f-ea902771bc.json')
# This is for the check of credential
default_app = firebase_admin.initialize_app(cred_obj,{"databaseURL":"https://mama-e0162-default-rtdb.asia-southeast1.firebasedatabase.app/"}) 
pb = pyrebase.initialize_app(json.load(open("C://Users//T490s//Downloads//fastAPI//database_connect_app//firebase_config.json")))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="Signin")

app = FastAPI()

class Keys(BaseModel):
	key: str
class Books(BaseModel):
	Author: Union[str,None] = None
	Genre: Union[str,None] = None
	Price: int = 100
	Title: str

class Account(BaseModel):
	Email: str
	Password: str = Path(min_length=6)

# Sign up
@app.post("/Signup", include_in_schema=True)
async def sign_up(account: Account = Depends()):
	Useremail = account.Email
	Userpassword = account.Password
	if Useremail == None or Userpassword == None:
		raise HTTPException(status_code=400, detail={'message': 'Error! Missing Email or Password'})
	# try:
	user = auth.create_user(email= Useremail, password= Userpassword)
	return  JSONResponse(status_code=200, content={'message':"Successfully Creating An Account {0}, and the link to verify {1}".format(user.uid,str(auth.generate_email_verification_link(email=Useremail)))})
	# except:
	# 	raise HTTPException(status_code=400, detail={'message': "Unsucessfully Creating An Account"})
	

# Signin
# This function is used to both sign in and play a role as a function to generate the token for OAuth2PasswordBearer
@app.post('/Signin',include_in_schema=True)
async def sign_in(request: Account = Depends() ):
	email = request.Email
	password = request.Password
	try:
		user = pb.auth().sign_in_with_email_and_password(email=email,password=password)
		jwt = user['idToken']
		if not pb.auth().get_account_info(id_token=jwt)['users'][0]['emailVerified']:
			return HTTPException(status_code=400, detail={'message':'Email needs to be verified first'})
		return {"access_token": jwt, "token_type": "bearer"}
	except:
		raise HTTPException(status_code=400, detail={'message': 'There was an error logging in'})




# To get the name of author
@app.get("/Books/Book_Author/{name_author}",response_model=list[Books])
async def func(*,token: str = Depends(oauth2_scheme),name_author: str):
	books_map = db.reference("Books").child("Best_Sellers").order_by_child("Author").equal_to(name_author).get()
	res = list()
	for key,value in books_map.items():
		res.append(Books(**value))
	return res

# This function is to locking the endpoint -> if the given token exactly specifies the account -> it will authorize
# user to use that endpoint (of course, users must give to the request the token)
async def authorization(token: str = Depends(oauth2_scheme)):
	credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
	try:
		pb.auth().get_account_info(token)
		return True
	except:
		raise credentials_exception



# To get book with the highest price whose price is more than or equal to {price}
@app.get("/Book/Book_Highest_Price", response_model= Union[Books,None])
async def get_highest_price(*,authenticated: bool = Depends(authorization),price: int):
	books_map = db.reference("Books").child("Best_Sellers").order_by_child("Price").start_at(price).limit_to_last(1).get()
	for key,value in books_map.items():
		return Books(**value)
	return None


# To get list of keys of Books
@app.get("/Book/Keys", response_model=list[Keys])
async def get_keys(book: Books = Depends()):
	books_map = db.reference("Books").child("Best_Sellers").order_by_child("Title").equal_to(book.Title).get()
	res = list()
	for key,value in books_map.items():
		if value["Genre"] == book.Genre and value["Price"] == book.Price and value["Author"] == book.Author:
			res.append(Keys(**{"key": key}))
	return res


@app.put("/Book/Update")
async def update_book(new_value: Books = Body(),old_book_keys: list[Keys] = Depends(get_keys)):
	for key in old_book_keys:
		db.reference("Books").child("Best_Sellers").child(key.key).get()
	return {"Status:": "Succesfully Update"}

@app.post("/Book")
async def add_more_book(book: Books = Depends()):
	mybook = db.reference("Books").child("Best_Sellers").push(dict(book)).get()
	return mybook 

# AbcE