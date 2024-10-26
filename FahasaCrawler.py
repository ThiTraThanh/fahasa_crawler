import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import re
from urllib.parse import urljoin, unquote
import hashlib

# hàm viết lại tên của ảnh dựa trên tên của page mình đọc được
def sanitize_filename(filename):
    # Loại bỏ các ký tự không hợp lệ trong tên file
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    # Rút gọn tên file nếu quá dài
    if len(filename) > 50:
        filename = filename[:47] + "..."
    return filename

# hàm tải ảnh nhưng t chạy không được nên chỉ lấy link ảnh thôi
def download_image(image_url, folder_path, book_title):
    try:
        # Tạo tên file từ tiêu đề sách
        safe_title = sanitize_filename(book_title)
        # Tạo mã hash từ URL để đảm bảo tên file unique
        hash_object = hashlib.md5(image_url.encode())
        file_extension = '.jpg'  # Fahasa thường dùng jpg
        image_filename = f"{safe_title}_{hash_object.hexdigest()[:8]}{file_extension}"
        image_path = os.path.join(folder_path, image_filename)
        
        # Kiểm tra nếu file đã tồn tại
        if os.path.exists(image_path):
            print(f"Ảnh đã tồn tại: {image_filename}")
            return image_filename
            
        # Tải ảnh
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        # Lưu ảnh
        with open(image_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    
        print(f"Đã tải ảnh: {image_filename}")
        return image_filename
        
    except Exception as e:
        print(f"Lỗi khi tải ảnh: {str(e)}")
        return None


def crawl_fahasa_books(base_url, limit=70):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
    }
    books_data = []
    page = 1
    books_crawled = 0
    
    # Tạo thư mục để lưu ảnh
    image_folder = 'fahasa_images'
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    while books_crawled < limit:
        try:
            # Tạo URL cho từng trang
            if page == 1:
                url = base_url
            else:
                url = f"{base_url}?p={page}"
                
            print(f"\nĐang crawl trang {page}...")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tìm tất cả các phần tử chứa thông tin sách
            books = soup.find_all('div', class_='ma-box-content')
            
            if not books:
                print(f"Không tìm thấy sách nào ở trang {page}")
                break

            for book in books:
                if books_crawled >= limit:
                    break
                    
                try:
                    # Kiểm tra và lấy tiêu đề và link
                    title_element = book.find('a', href=True)
                    if not title_element:
                        continue
                        
                    title = title_element.get('title', 'Không có tiêu đề')
                    link = title_element.get('href', '')
                    
                    if not link:
                        continue

                    print(f"\nĐang crawl cuốn thứ {books_crawled + 1}: {title}")
                    
                    # Thêm delay để tránh request quá nhanh
                    time.sleep(1.5)
                    
                    # Lấy thông tin chi tiết sách
                    book_response = requests.get(link, headers=headers)
                    book_response.raise_for_status()
                    book_soup = BeautifulSoup(book_response.content, 'html.parser')

                    def get_text_safe(element, default='Không có thông tin'):
                        return element.text.strip() if element else default

                    # Lấy thông tin với xử lý None
                    description_elem = book_soup.find('div', id='desc_content')
                    description = get_text_safe(description_elem)
                    
                    # Lấy giá hiện tại
                    price_elem = book_soup.find('p', class_='special-price').find('span', class_='price')
                    price = get_text_safe(price_elem)
                    
                    # Lấy giá gốc
                    old_price_elem = book_soup.find('p', class_='old-price').find('span', class_='price')
                    old_price = get_text_safe(old_price_elem)
                    
                    provider_elem = book_soup.find('td', class_='data_supplier')
                    provider = get_text_safe(provider_elem)
                    
                    author_elem = book_soup.find('td', class_='data_author')
                    author = get_text_safe(author_elem)
                    
                    translator_elem = book_soup.find('td', class_='data_translator')
                    translator = get_text_safe(translator_elem)
                    
                    publisher_elem = book_soup.find('td', class_='data_publisher')
                    publisher = get_text_safe(publisher_elem)
                    
                    publish_year_elem = book_soup.find('td', class_='data_publish_year')
                    publish_year = get_text_safe(publish_year_elem)
                    
                    cover_type_elem = book_soup.find('td', class_='data_book_layout')
                    cover_type = get_text_safe(cover_type_elem)
                    
                    # image_elem = book_soup.find('img', class_='swiper-lazy swiper-lazy-loaded')
                    # image = image_elem.get('src', 'Không có hình ảnh') if image_elem else 'Không có hình ảnh'
                    image_url = book_soup.find('img', class_='swiper-lazy')['src']
                    # image_url = image_elem['src'] if image_elem else ''
                    # local_image_path = None
                    
                    # if image_url:
                    #     local_image_path = download_image(image_url, image_folder, title)
                    books_data.append({
                        'STT': books_crawled + 1,
                        'Tên Sản Phẩm': title,
                        'Giá Hiện Tại': price,
                        'Giá Gốc': old_price,
                        'Nhà Cung Cấp': provider,
                        'Tác Giả': author,
                        'Người Dịch': translator,
                        'Nhà Xuất Bản': publisher,
                        'Năm Xuất Bản': publish_year,
                        'Hình Thức': cover_type,
                        'Link Sản Phẩm': link,
                        'Hình Ảnh': image_url,
                        'Mô Tả': description,
                        # 'Ảnh Đã Tải': local_image_path if local_image_path else 'Không tải được'
                    })
                    
                    books_crawled += 1
                    print(f"Đã crawl thành công: {books_crawled}/{limit} cuốn")
                    
                except requests.RequestException as e:
                    print(f"Lỗi khi request trang chi tiết sách: {e}")
                    continue
                except Exception as e:
                    print(f"Lỗi khi xử lý sách: {str(e)}")
                    continue
            
            page += 1
            
        except requests.RequestException as e:
            print(f"Lỗi khi request trang {page}: {e}")
            break
        except Exception as e:
            print(f"Lỗi không mong muốn ở trang {page}: {str(e)}")
            break
            
    print(f"\nĐã hoàn thành! Crawl được {len(books_data)} cuốn sách")
    return books_data

def save_to_csv(books_data, filename='fahasa_books.csv'):
    if not books_data:
        print("Không có dữ liệu để lưu")
        return
        
    try:
        with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(file, fieldnames=books_data[0].keys())
            writer.writeheader()
            for book in books_data:
                writer.writerow(book)
        print(f"Đã lưu dữ liệu thành công vào {filename}")
    except Exception as e:
        print(f"Lỗi khi lưu file CSV: {str(e)}")

# Sử dụng code
url = 'https://www.fahasa.com/sach-trong-nuoc/dam-my.html'  # Thay đổi URL theo nhu cầu
books_data = crawl_fahasa_books(url, limit=70)  # Giới hạn 70 cuốn
if books_data:
    save_to_csv(books_data, 'fahasa_books_70_6.csv')