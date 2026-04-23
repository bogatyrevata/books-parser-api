# tests/test_api.py

# --- ТЕСТЫ КАТЕГОРИЙ ---

def test_get_categories_empty(client):
    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json() == []

def test_create_category(client):
    response = client.post("/categories", json={"name": "Fiction"})
    assert response.status_code == 201
    assert response.json()["name"] == "Fiction"
    assert "id" in response.json()

def test_create_category_duplicate(client):
    client.post("/categories", json={"name": "Horror"})
    response = client.post("/categories", json={"name": "Horror"})
    assert response.status_code == 400

def test_get_category_not_found(client):
    response = client.get("/categories/99999")
    assert response.status_code == 404


# --- ТЕСТЫ КНИГ ---

def test_create_book(client):
    response = client.post("/books", json={
        "title": "Test Book",
        "url": "http://test.com/book1",
        "price": 9.99,
        "in_stock": True,
        "rating": 4,
        "category_id": None
    })
    assert response.status_code == 201
    assert response.json()["title"] == "Test Book"

def test_create_book_duplicate(client):
    data = {
        "title": "Duplicate",
        "url": "http://test.com/duplicate",
        "price": 9.99,
        "in_stock": True,
        "rating": 4,
        "category_id": None
    }
    client.post("/books", json=data)
    response = client.post("/books", json=data)
    assert response.status_code == 400

def test_get_book_not_found(client):
    response = client.get("/books/99999")
    assert response.status_code == 404

def test_patch_book(client):
    response = client.post("/books", json={
        "title": "Old Title",
        "url": "http://test.com/patch",
        "price": 5.99,
        "in_stock": True,
        "rating": 3,
        "category_id": None
    })
    book_id = response.json()["id"]
    response = client.patch(f"/books/{book_id}", json={"price": 1.99})
    assert response.status_code == 200
    assert response.json()["price"] == 1.99
    assert response.json()["title"] == "Old Title"

def test_delete_book(client):
    response = client.post("/books", json={
        "title": "Delete Me",
        "url": "http://test.com/delete",
        "price": 5.99,
        "in_stock": True,
        "rating": 3,
        "category_id": None
    })
    book_id = response.json()["id"]
    client.delete(f"/books/{book_id}")
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 404