from flask import Flask, jsonify, render_template, request, redirect, url_for
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

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
    return render_template('index.html')

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
