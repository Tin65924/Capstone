from app.cataloging.models import (
    get_all_books, search_books, get_book_by_id, create_book,
    update_book, update_book_status, delete_book, create_accession,
    get_accessions_by_book, get_accession_by_number,
    search_books_paginated
)
from app.auth.models import log_activity

print(get_book = get_book_by_id())