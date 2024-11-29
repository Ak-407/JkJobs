from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import numpy as np
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from authlib.integrations.flask_client import OAuth
import hashlib
import os


from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key = 'parrot'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)




login_manager = LoginManager(app)
login_manager.login_view = 'login'


oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id='643204173482-2ug4dnd8s1utm2go2i3ouucolnkn2dol.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v2/',
    client_kwargs={'scope': 'openid email profile'},
    redirect_uri=os.getenv('GOOGLE_REDIRECT_URI', 'http://127.0.0.1:5000/authorize'),
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs'  # Explicitly set jwks_uri
)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # Store hashed passwords
    email = db.Column(db.String(100), unique=True)

# Routes
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Hash the password with MD5
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
        
#         # Hash the password with MD5
#         hashed_password = hashlib.md5(password.encode()).hexdigest()
        
#         user = User.query.filter_by(username=username, password=hashed_password).first()
#         if user:
#             login_user(user)
#             return redirect(url_for('index'))
#         return "Invalid username or password"
#     return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash the password with MD5
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        # Check if user exists
        user = User.query.filter_by(username=username, password=hashed_password).first()
        if user:
            login_user(user)
            session['username'] = username  # Store username in the session
            return redirect(url_for('index'))
        return "Invalid username or password"
    return render_template('login.html')




@app.route('/google-login')
def google_login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()  # Access token
    user_info = google.get('userinfo').json()  # Get user info

    # If the OAuth flow gives back the id_token, you can use it here
    id_token = token.get('id_token')

    # Verify the token if needed
    # (optional) Add logic to verify the id_token using the jwks_uri

    # Check if the user already exists in the DB
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(username=user_info['name'], email=user_info['email'], password='')
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    return f"Welcome, {current_user.username}! <a href='/logout'>Logout</a>"

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('username', None)
    return redirect(url_for('login'))












class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(50), nullable=False)
    job_location = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(50), nullable=False)
    salary = db.Column(db.String(50), nullable=False)
    eligibility = db.Column(db.String(100), nullable=False)
    industry_type = db.Column(db.String(100), nullable=False)
    functional_area = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.Text, nullable=False)












def gkscrape_news():
    gknews_list = []
    url = 'https://www.bbc.com/news/topics/cx1m7zg0wwzt'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    gkresponse = requests.get(url, headers=headers)

    if gkresponse.status_code == 200:
        gksoup = BeautifulSoup(gkresponse.content, 'html.parser')

        # Adjust class name according to actual structure
        gkarticles = gksoup.find_all('div', {'class': 'sc-ae29827d-4 ypQFr'})  

        for gkarticle in gkarticles:
            gktitle_tag = gkarticle.find('h2', {'class': 'sc-8ea7699c-3 gRBdkE'})
            gktitle_text = gktitle_tag.text.strip() if gktitle_tag else 'No title available'
            print(gktitle_text)
            
            gkdescription_tag = gkarticle.find('p', {'class': 'sc-ae29827d-0 cNPpME'})
            gkdescription_text = gkdescription_tag.text.strip() if gkdescription_tag else 'No description available'
            
            gkimage_tag = gkarticle.find('img',{'class':'sc-a34861b-0 efFcac'})
            gkimage_url = gkimage_tag['src'] if gkimage_tag else '/static/m.png'
            
            gklink_tag = gkarticle.find('a', {'data-testid': 'internal-link'})
            gklink_url = "https://www.bbc.com" + gklink_tag['href'] if gklink_tag else 'No link available'
            
            gknews_list.append({
                'gktitle': gktitle_text,
                'gkdescription': gkdescription_text,
                'gkimage_url': gkimage_url,
                'gklink_url': gklink_url
            })

        return gknews_list
    else:
        return []

@app.route('/api/gknews')
def get_gknews():
    return jsonify(gkscrape_news())

















def scrape_news():
    url = 'https://www.bing.com/news/search?q=kashmir&qs=n&form=QBNT&sp=-1&lq=0&pq=kashm&sc=10-5&sk=&cvid=0851B772B9E44B47A08030C01F2F8521&ghsh=0&ghacc=0&ghpl='
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find_all('div', class_='news-card')

        news_list = []
        for article in articles[:30]:
            title_tag = article.find('a', class_='title')
            title_text = title_tag.get_text() if title_tag else "No title available"

            image_tag = article.find('img', class_='rms_img')
            image_url = "https:" + image_tag['data-src-hq'] if image_tag and 'data-src-hq' in image_tag.attrs else "/static/m.png"

            link_tag = article.find('a', class_='title')
            link_url = link_tag['href'] if link_tag and 'href' in link_tag.attrs else "#"
            if link_tag and 'href' in link_tag.attrs:
                base_url = link_tag['href'].split("//")[1].split("/")[0]
            else:
                base_url = "#"

            source_tag = article.find('a', class_='biglogo_link')
            source_text = source_tag['title'] if source_tag and 'title' in source_tag.attrs else "No source available"

            description = article.find('div', class_='snippet')
            desc = description.get_text() if description else "No description available"

            news_list.append({
                'title': title_text,
                'image_url': image_url if image_url != "No image available" else image_url,
                'base_url': base_url,
                'link': link_url,
                'desc': desc,
            })

        return news_list
    else:
        return []


def scrape_articles():
    urls = [
        'https://jkalerts.com/category/jammu-kashmir-jobs/govt-jobs-india/',
        'https://jkalerts.com/category/jammu-kashmir-jobs/'
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    articles_data = []
    
    for url in urls:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('article', class_='post')
            
            if not articles:
                continue

            for article in articles:
                time_tag = article.find('div', class_='post-date-ribbon')
                time_text = time_tag.get_text() if time_tag else "No date available"

                title_tag = article.find('h2', class_='title')
                title_text = title_tag.get_text() if title_tag else "No title available"

                info_tag = article.find('div', class_='post-info')
                info_text = info_tag.get_text() if info_tag else "No information available"

                image_tag = article.find('img', class_='attachment-ribbon-lite-featured size-ribbon-lite-featured wp-post-image')
                if image_tag:
                    image_url = image_tag.get('src', image_tag.get('/static/m.png', "No image available"))
                else:
                    image_url = '/static/m.png'


                content_tag = article.find('div', class_='post-content')
                content_text = content_tag.get_text() if content_tag else "No content available"

                read_more_tag = article.find('div', class_='readMore').find('a')
                read_more_url = read_more_tag['href'] if read_more_tag and 'href' in read_more_tag.attrs else "#"
                read_more_title = read_more_tag['title'] if read_more_tag and 'title' in read_more_tag.attrs else "Read More"

                articles_data.append({
                    'title': title_text,
                    'image_url': image_url,
                    'info': info_text,
                    'content': content_text,
                    'date': time_text,
                    'link': read_more_url,
                    'read_more_title': read_more_title
                })

        else:
            return {'error': f'Failed to retrieve the articles from {url}'}

    if not articles_data:
        return {'error': 'No articles found from both sources'}

    return articles_data


@app.route('/news-details1')
def news_details1():
    news_link1 = request.args.get('news_link1')
    if not news_link1:
        return 'news1 link is missing', 400

    if not news_link1.startswith(('http://', 'https://')):
        news_link1 = 'https://' + news_link1

    soup = scrape_page(news_link1)
    if soup:
        news_info1 = extract_news_details1(soup,news_link1)
        if news_info1:
            return render_template('index3.html', news_info1=news_info1)
    return f'news1 details not found with url {news_link1}', 404



def extract_news_details1(soup,url):
    try:

        if 'jkalerts.com' in url:
            # For URLs containing jkalerts.com
            news_title1 = soup.select_one('h1.title')
            news_title_text1 = news_title1.text.strip() if news_title1 else "No title available"

            description1 = soup.select_one('p')
            description_text1 = description1.text.strip() if description1 else "No description available"

            content_tag = soup.find('div', class_="tags")
            tags = content_tag.find('a') if content_tag else None
            tag = tags.text.strip() if tags else "No tags available"
            # print("Description:", description_text1)

        else:
            # For URLs containing bing.com/news
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            ar= soup.find_all('article', class_='article-reader-container')
            print(ar)
            news_title1 = soup.select_one('h1.viewsHeaderText')
            news_title_text1 = news_title1.text.strip() if news_title1 else "No title available"
            print(news_title1)

            description1 = soup.select_one('p')
            description_text1 = description1.text.strip() if description1 else "No description available"

            content_tag = soup.find('body', class_="article-body")
            tags = content_tag.find('p') if content_tag else None
            tag = tags.text.strip() if tags else "No tags available"



        return {
            'title': news_title_text1,
            'description': description_text1,
            'tag':tag,
            'url':url
        }
    except Exception as e:
        print(f"Error extracting news details: {str(e)}")
































































































def scrape_articles2():
    url = 'https://jkalerts.com/category/jammu-kashmir-news/kashmir-news/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    articles_data2 = []

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find_all('article', class_='post')

        if not articles:
            return []

        for article in articles:
            time_tag = article.find('div', class_='post-date-ribbon')
            time_text = time_tag.get_text() if time_tag else "No date available"

            title_tag = article.find('h2', class_='title')
            title_text = title_tag.get_text() if title_tag else "No title available"

            info_tag = article.find('div', class_='post-info')
            info_text = info_tag.get_text() if info_tag else "No information available"

            image_tag = article.find('img', class_='attachment-ribbon-lite-featured size-ribbon-lite-featured wp-post-image')
            image_url = image_tag['src'] if image_tag and 'src' in image_tag.attrs else "No image available"

            content_tag = article.find('div', class_='post-content')
            content_text = content_tag.get_text() if content_tag else "No content available"

            read_more_tag = article.find('div', class_='readMore').find('a')
            read_more_url = read_more_tag['href'] if read_more_tag and 'href' in read_more_tag.attrs else "#"
            read_more_title = read_more_tag['title'] if read_more_tag and 'title' in read_more_tag.attrs else "Read More"

            articles_data2.append({
                'title': title_text,
                'image_url': image_url,
                'info': info_text,
                'content': content_text,
                'date': time_text,
                'read_more_url': read_more_url,
                'read_more_title': read_more_title
            })
    else:
        return {'error': f'Failed to retrieve the articles from {url}'}

    if not articles_data2:
        return {'error': 'No articles found'}

    return articles_data2

@app.route('/news-details')
def news_details():
    news_link = request.args.get('news_link')
    if not news_link:
        return 'news link is missing', 400

    if not news_link.startswith(('http://', 'https://')):
        news_link = 'https://' + news_link

    soup = scrape_page(news_link)
    if soup:
        news_info = extract_news_details(soup,news_link)
        if news_info:
            return render_template('index4.html', news_info=news_info)
    return f'news details not found with url {news_link}', 404

def scrape_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.content, 'html.parser')
    return None

def extract_news_details(soup,url):
    try:
        news_title = soup.select_one('h1.title')
        news_title_text = news_title.text.strip() if news_title else "No title available"

        description = soup.select_one('p')
        description_text = description.text.strip() if description else "No description available"




        # content_div = soup.find('div', id='content')
    
        # if content_div:
        #     # Find all 'p' elements within the 'div'
        #     paragraphs = content_div.find_all('p')
            
    
        #     if paragraphs:
        #         for idx, paragraph in enumerate(paragraphs, start=1):
        #             # Extract and clean the text
        #             description_text = paragraph.text.strip()
        #             print(f"Description {idx}:", description_text)
        #     else:
        #         print("No paragraph elements found within the content div.")
        # else:
        #     print("No content div found with id='content'.")


        # tags = soup.select_one('div', class_="tags")
        # tag = tags.text.strip() if tags else "No tags available"

        content_tag = soup.find('div', class_="tags")
        tags = content_tag.find('a') if content_tag else None
        tag = tags.text.strip() if tags else "No tags available"
        print("Description:", description_text)




        return {
            'title': news_title_text,
            'description': description_text,
            'tag':tag,
            'url':url
        }
    except Exception as e:
        print(f"Error extracting news details: {str(e)}")





































































def scrape_job_postings():
    url = 'https://linkingsky.com/government-exams/government-jobs-in-jammu-and-kashmir.html'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        table_rows = soup.find_all('tr', class_='top_job')

        job_list = []
        for row in table_rows:
            post_date = row.find('td', {'data-title': 'Post Date'}).get_text(strip=True)
            organization_td = row.find('td', {'data-title': 'Organization'})
            organization_name = organization_td.get_text(strip=True)
            organization_link_tag = organization_td.find('a')
            organization_link = organization_link_tag['href'] if organization_link_tag else "No link available"
            
            if organization_link != "No link available":
                parsed_url = urlparse(organization_link)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            else:
                base_url = organization_link

            posts = row.find('td', {'data-title': 'Posts'}).get_text(strip=True)
            qualification = row.find('td', {'data-title': 'Qualification'}).get_text(strip=True)
            last_date = row.find('td', {'data-title': 'Last Date'}).get_text(strip=True)

            job_list.append({
                'post_date': post_date,
                'organization': organization_name,
                'posts': posts,
                'qualification': qualification,
                'last_date': last_date,
                'link': base_url
            })

        return job_list
    else:
        return []


def scrape_articles4():
    urls = [
        'https://jkalerts.com/category/jammu-kashmir-notifications/'
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    articles_data = []
    
    for url in urls:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('article', class_='post')
            
            if not articles:
                continue

            for article in articles:

                title_tag = article.find('h2', class_='title')
                title_text = title_tag.get_text() if title_tag else "No title available"

                articles_data.append({
                    'title': title_text,
                })

        else:
            return {'error': f'Failed to retrieve the articles from {url}'}

    if not articles_data:
        return {'error': 'No articles found from both sources'}

    return articles_data

def scrape_articles5():
    urls = [
        'https://jkalerts.com/category/jammu-kashmir-jobs/jk-jobs-updates/'
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    articles_data = []
    
    for url in urls:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('article', class_='post')
            
            if not articles:
                continue

            for article in articles:

                title_tag = article.find('h2', class_='title')
                title_text = title_tag.get_text() if title_tag else "No title available"

                articles_data.append({
                    'title': title_text,
                })

        else:
            return {'error': f'Failed to retrieve the articles from {url}'}

    if not articles_data:
        return {'error': 'No articles found from both sources'}

    return articles_data




def scrape_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {url}: {str(e)}")
        return None














@app.route('/scrape')
def scrape():
    page_number = int(request.args.get('page', 1))
    query = request.args.get('q', '')
    base_url = "https://www.google.com/about/careers/applications/jobs/results"
    url = f"{base_url}?start={166 * (page_number - 1)}"

    if query:
        url += f"&q={query}"

    soup = scrape_page(url)
    if soup:
        job_elements = soup.select('div.sMn82b')
        jobs = []
        for job in job_elements[:3]:
            try:
                title_element = job.select_one('h3.QJPWVe')
                title = title_element.text if title_element else "No title found"
                
                place_elements = job.select('span.r0wTof')
                places = [element.text for element in place_elements if element.text]
                place = ", ".join(places) if places else "No location found"
                
                qualifications_element = job.select_one('div.Xsxa1e')
                qualifications_list = qualifications_element.select('ul li') if qualifications_element else []
                qualifications = [li.text for li in qualifications_list if li.text]
                
                # Extract the job link
                link_element = job.select_one('a[jsname="hSRGPd"]')
                job_link = link_element['href'] if link_element else "#"
                
                # Ensure the URL is absolute
                if job_link.startswith('/'):
                    job_link = f"https://www.google.com{job_link}"
                
                job_info = {
                    'title': title,
                    'place': place,
                    'qualifications': qualifications,
                    'link': job_link
                }
                jobs.append(job_info)
            except Exception as e:
                print(f"Error processing job element: {str(e)}")
                continue
        return jsonify(jobs)
    return jsonify({'error': 'Failed to retrieve data'}), 500

@app.route('/job-details')
def job_details():
    job_link = request.args.get('job_link')
    if not job_link:
        return 'Job link is missing', 400

    if not job_link.startswith(('http://', 'https://')):
        job_link = 'https://www.google.com/about/careers/applications/' + job_link

    soup = scrape_page(job_link)
    if soup:
        # Log the raw HTML content for debugging
        with open('debug.html', 'w', encoding='utf-8') as file:
            file.write(soup.prettify())
        job_info = extract_job_details(soup)
        if job_info:
            return render_template('index2.html', job_info=job_info)
    return f'Job details not found with url {job_link}', 404



def extract_job_details(soup):
    try:
        job_title = soup.select_one('h2.p1N2lc').text.strip()  # Update with correct selector
        location = soup.select_one('span.r0wTof').text.strip()  # Update with correct selector
        qualifications = [li.text.strip() for li in soup.select('div.KwJkGe')]  # Update with correct selector
        description = soup.select_one('div.aG5W3 > p').text.strip()  # Update with correct selector

        # Extract the Apply button URL
        apply_button = soup.select_one('a#apply-action-button')
        apply_url = apply_button['href'] if apply_button and 'href' in apply_button.attrs else None
        
        return {
            'title': job_title,
            'location': location,
            'qualifications': qualifications,
            'description': description,
            'apply_url': 'https://www.google.com/about/careers/applications/'+apply_url  # Add the Apply URL to the result
        }
    except AttributeError as e:
        print(f"Error extracting job details: {str(e)}")
        return None


@app.route('/')
def index():
    username = session.get('username')
    return render_template('index.html', username=username)

@app.route('/improveresume')
def index3449():
    return render_template('improveresume.html')


@app.route('/index2.html')
def index2():
    return render_template('index2.html')

@app.route('/index4.html')
def index3():
    return render_template('index4.html')

@app.route('/index3.html')
def index4():
    return render_template('index3.html')

@app.route('/job-posting')
def index5():
    jobs = Job.query.all()
    return render_template('job-posting.html', jobs=jobs)



@app.route('/jobform')
def index6():
    return render_template('jobform.html')



@app.route('/postjob', methods=['POST'])
def post_job():
    job_type = request.form['job_type']
    job_location = request.form['job_location']
    experience = request.form['experience']
    salary = request.form['salary']
    eligibility = request.form['eligibility']
    industry_type = request.form['industry_type']
    functional_area = request.form['functional_area']
    skills = request.form['skills']

    new_job = Job(
        job_type=job_type,
        job_location=job_location,
        experience=experience,
        salary=salary,
        eligibility=eligibility,
        industry_type=industry_type,
        functional_area=functional_area,
        skills=skills
    )

    db.session.add(new_job)
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/api/news')
def get_articles():
    articles = scrape_articles()
    news = scrape_news()
    combined_data = articles + news
    return jsonify(combined_data)

@app.route('/api/gknews')
def gkget_articles():
    gknews = gkscrape_news()
    return jsonify(gknews)


@app.route('/api/news2')
def get_articles2():
    news2 = scrape_articles2()
    return jsonify(news2)

@app.route('/api/news3')
def get_articles3():
    news3 = scrape_job_postings()
    return jsonify(news3)

@app.route('/api/news4')
def get_articles4():
    news4 = scrape_articles4()
    return jsonify(news4)


@app.route('/api/news5')
def get_articles5():
    news5 = scrape_articles5()
    return jsonify(news5)


# if __name__ == '__main__':
#     app.run(debug=True)
































































from flask import Flask, request, render_template
import pickle
import docx
import PyPDF2
import re

# Load the machine learning model and encoders
svc_model = pickle.load(open('clf.pkl', 'rb'))
tfidf = pickle.load(open('tfidf.pkl', 'rb'))
le = pickle.load(open('encoder.pkl', 'rb'))


def cleanResume(txt):
    cleanText = re.sub(r'http\S+\s', ' ', txt)
    cleanText = re.sub(r'RT|cc', ' ', cleanText)
    cleanText = re.sub(r'#\S+\s', ' ', cleanText)
    cleanText = re.sub(r'@\S+', '  ', cleanText)
    cleanText = re.sub(r'[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', cleanText)
    cleanText = re.sub(r'[^\x00-\x7f]', ' ', cleanText)
    cleanText = re.sub(r'\s+', ' ', cleanText)
    return cleanText

# Function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ''
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text

# Function to extract text from TXT with explicit encoding handling
def extract_text_from_txt(file):
    try:
        text = file.read().decode('utf-8')
    except UnicodeDecodeError:
        text = file.read().decode('latin-1')
    return text

# Function to handle file upload and extraction
def handle_file_upload(uploaded_file):
    file_extension = uploaded_file.filename.split('.')[-1].lower()
    if file_extension == 'pdf':
        text = extract_text_from_pdf(uploaded_file)
    elif file_extension == 'docx':
        text = extract_text_from_docx(uploaded_file)
    elif file_extension == 'txt':
        text = extract_text_from_txt(uploaded_file)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF, DOCX, or TXT file.")
    return text

# Function to predict the category of a resume
def pred(input_resume):
    cleaned_text = cleanResume(input_resume)
    vectorized_text = tfidf.transform([cleaned_text]).toarray()
    predicted_category = svc_model.predict(vectorized_text)
    predicted_category_name = le.inverse_transform(predicted_category)
    return predicted_category_name[0], predicted_category  # Return category and prediction score

# Function to calculate ATS score based on job keywords
def calculate_ats_score(resume_text, job_keywords):
    if len(job_keywords) == 0:
        return 0.0
    
    match_count = sum(1 for keyword in job_keywords if keyword.lower() in resume_text.lower())

    if match_count == 0:
        return 0.0

    ats_score = (match_count / len(job_keywords)) * 100

    # Ensure ats_score is numeric
    if isinstance(ats_score, (int, float)):
        return round(ats_score, 2)
    else:
        print(f"Error: Invalid ats_score type: {type(ats_score)}")  # Debugging log
        return 0.0



# Function to calculate ATS score based on model prediction confidence
import numpy as np

# Function to calculate ATS score based on model prediction confidence
import numpy as np

def calculate_model_ats_score(prediction_score):
    print(f"Debug: prediction_score type = {type(prediction_score)}")
    print(f"Debug: prediction_score = {prediction_score}")

    # Check if prediction_score is a list, numpy array, or similar iterable
    if isinstance(prediction_score, (list, np.ndarray)):
        if len(prediction_score) > 0:
            confidence_score = max(prediction_score)  # Get the maximum score
            print(f"Debug: confidence_score = {confidence_score}")

            # Check if confidence_score is numeric
            if isinstance(confidence_score, (int, float)):
                ats_score = confidence_score * 100
                print(f"Debug: ats_score = {ats_score}")
                return round(ats_score, 2)  # Round to 2 decimal places
            else:
                print(f"Error: confidence_score is not numeric: {confidence_score}")
                return 0.0  # Return a default value if not numeric
        else:
            print("Error: prediction_score is an empty list/array.")
            return 0.0
    else:
        print(f"Error: prediction_score is not a list or array: {prediction_score}")
        return 0.0


@app.route('/resume', methods=['GET', 'POST'])
def handle_resume():
    if request.method == 'POST':
        # Handling POST request: File upload
        resume_file = request.files['resume']
        
        # Use the handle_file_upload function to extract text from the uploaded file
        resume_text = handle_file_upload(resume_file)
        
        job_keywords = ['python', 'machine learning', 'data science']  # Example keywords
        ats_score_keywords = calculate_ats_score(resume_text, job_keywords)
        
        # Example prediction score
        prediction_score = [0.85]
        ats_score_model = calculate_model_ats_score(prediction_score)
        
        # Extract experience and skills
        experience = extract_experience(resume_text)
        skills = extract_skills(resume_text)
        
        # Predict category of the resume
        category, _ = pred(resume_text)
        
        return render_template('resume.html', 
                               category=category, 
                               ats_score_keywords=ats_score_keywords, 
                               ats_score_model=ats_score_model, 
                               experience=experience, 
                               skills=skills, 
                               resume_text=resume_text)
    else:
        # Handling GET request: Render the form for resume upload
        return render_template('resume.html')
# Function to extract experience details from resume text
def extract_experience(text):
    experience = re.findall(r'(\d+)\s?years?\s?(of\s?experience)?', text, re.IGNORECASE)
    return experience

# Function to extract skills from resume text
def extract_skills(text):
    skills = re.findall(r'\b(Python|Java|C\+\+|JavaScript|SQL|HTML|CSS)\b', text, re.IGNORECASE)
    return skills




import json

from flask import Flask, render_template, request, jsonify
import torch
import random
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize


# Load model and data
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

bot_name = "Amaan"

@app.route("/chat")
def home():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    sentence = tokenize(user_message)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)

    tag = tags[predicted.item()]
    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]

    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent["tag"]:
                response = random.choice(intent['responses'])
                return jsonify({"bot": response})
    else:
        return jsonify({"bot": "I do not understand...Write full question"})






































# deactivate
# python -m venv myenv
# source myenv/bin/activate






if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5900)))

    # app.run(debug=True, port=8050, host='0.0.0.0')
