from gazpacho import get, Soup

url = "http://www.puzzles.grosse.is-a-geek.com/uberarchive.html"
html = get(url)

soup = Soup(html)

tables = soup.find('center')[2]

with open ('tables.html', 'w') as f:
    f.write(str(tables))
    f.close()


