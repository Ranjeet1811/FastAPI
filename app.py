from typing import List, Optional, Tuple  
from fastapi import FastAPI, HTTPException, Query  
from pydantic import BaseModel 
import sqlite3  
from geopy.distance import geodesic  

app = FastAPI()  

class Address(BaseModel):  # Defining a Pydantic model for Address data
    id: Optional[int] = None  
    street: str
    city: str
    state: str
    country: str
    coordinates: Tuple[float, float]  

class AddressInDB(Address):  # Inheriting from Address, adding an id field
    id: int

def create_address_table():  # Function to create an SQLite table for addresses
    conn = sqlite3.connect('address_book.db')  
    c = conn.cursor()  
    # Creating addresses table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS addresses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, street TEXT, city TEXT,
                 state TEXT, country TEXT, latitude REAL, longitude REAL)''')
    conn.commit()  
    conn.close()  

def add_address_to_db(address: Address):  # Function to add an address to the database
    conn = sqlite3.connect('address_book.db')  
    c = conn.cursor()  
    # Inserting address data into addresses table
    c.execute("INSERT INTO addresses (street, city, state, country, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)",
              (address.street, address.city, address.state, address.country, *address.coordinates))
    conn.commit()  
    address_id = c.lastrowid  
    conn.close() 
    return address_id  

def get_address_from_db(address_id: int) -> AddressInDB:  # Function to get an address from the database
    conn = sqlite3.connect('address_book.db')  
    c = conn.cursor()  
    # Selecting address data from addresses table based on id
    c.execute("SELECT * FROM addresses WHERE id=?", (address_id,))
    result = c.fetchone()  
    conn.close()  
    if result:  
        return AddressInDB(id=result[0], street=result[1], city=result[2], state=result[3], country=result[4],
                           coordinates=(result[5], result[6]))
    else:  
        raise HTTPException(status_code=404, detail="Address not found")  # Raising 404 exception

def delete_address_from_db(address_id: int):  
    conn = sqlite3.connect('address_book.db')  
    c = conn.cursor() 
    
    c.execute("DELETE FROM addresses WHERE id=?", (address_id,))
    conn.commit()  
    conn.close()  

def update_address_in_db(address_id: int, address: Address):  # Function to update an address in the database
    conn = sqlite3.connect('address_book.db')  
    c = conn.cursor()  
    # Updating address data in addresses table based on id
    c.execute("UPDATE addresses SET street=?, city=?, state=?, country=?, latitude=?, longitude=? WHERE id=?",
              (address.street, address.city, address.state, address.country, *address.coordinates, address_id))
    conn.commit()  
    conn.close()  

def get_addresses_within_distance(latitude: float, longitude: float, distance: float) -> List[AddressInDB]:
    # Function to get addresses within a certain distance from a given location
    conn = sqlite3.connect('address_book.db')  
    c = conn.cursor()  
    c.execute("SELECT * FROM addresses")  
    all_addresses = c.fetchall()  
    conn.close()  
    addresses_within_distance = []  
    for address in all_addresses:  
        address_coordinates = (address[5], address[6])  
        
        if geodesic(address_coordinates, (latitude, longitude)).km <= distance:
           
            addresses_within_distance.append(AddressInDB(id=address[0], street=address[1], city=address[2],
                                                         state=address[3], country=address[4],
                                                         coordinates=address_coordinates))
    return addresses_within_distance  # Returning addresses within distance

@app.post("/addresses/", response_model=AddressInDB)  # POST endpoint to create an address
async def create_address(address: Address):
    address_id = add_address_to_db(address)  
    return get_address_from_db(address_id)  



@app.get("/addresses/{address_id}", response_model=AddressInDB)  # GET endpoint to read an address
async def read_address(address_id: int):
    return get_address_from_db(address_id)  


@app.put("/addresses/{address_id}", response_model=AddressInDB)  # PUT endpoint to update an address
async def update_address(address_id: int, address: Address):
    if get_address_from_db(address_id):  
        update_address_in_db(address_id, address)  
        return get_address_from_db(address_id)  

@app.delete("/addresses/{address_id}")  # DELETE endpoint to delete an address
async def delete_address(address_id: int):
    if get_address_from_db(address_id):  
        delete_address_from_db(address_id)  
        return {"message": "Address deleted successfully"}  

@app.get("/addresses/")  # GET endpoint to get addresses within a certain distance
async def get_addresses_within_radius(latitude: float = Query(..., description="Latitude of the location"),
                                      longitude: float = Query(..., description="Longitude of the location"),
                                      distance: float = Query(..., description="Distance in kilometers")):
    return get_addresses_within_distance(latitude, longitude, distance)  


create_address_table()  