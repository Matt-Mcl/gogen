from gazpacho import get, Soup

with open ('tables.html', 'r') as f:
    html = f.read()
    f.close()

soup = Soup(html)

uber = soup.find('table')[0].find('tr')[2:]

print(uber[0].find('a')[0].attrs.get('href'))

for u in uber:
    links = u.find('a')
    puzzle_link = links[0].attrs.get('href')
    solution_link = links[1].attrs.get('href')

    print(f"http://www.puzzles.grosse.is-a-geek.com/{puzzle_link}")

    puzzle_image = get(f"http://www.puzzles.grosse.is-a-geek.com/{puzzle_link}")

    print(puzzle_image)

    break
