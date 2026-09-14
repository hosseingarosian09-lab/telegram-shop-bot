from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Category, Product


BOOK_CATALOG = [{'name': '📖 رمان و داستان',
  'slug': 'fiction',
  'books': [('The Alchemist',
             'Paulo Coelho',
             285000,
             12,
             'A philosophical adventure about following a personal dream and paying attention to the lessons found '
             'along the journey.'),
            ('The Little Prince',
             'Antoine de Saint-Exupery',
             220000,
             18,
             'A short, imaginative story about friendship, responsibility, curiosity, and seeing beyond appearances.'),
            ('The Kite Runner',
             'Khaled Hosseini',
             390000,
             7,
             'A dramatic story of friendship, guilt, family, and redemption set across changing periods of Afghan '
             'history.'),
            ('The Book Thief',
             'Markus Zusak',
             420000,
             9,
             'A moving historical novel about a young reader, a foster family, and the power of words during wartime '
             'Germany.'),
            ('The Midnight Library',
             'Matt Haig',
             365000,
             0,
             'A speculative novel about regret, alternate possibilities, and reconsidering what can make a life '
             'meaningful.'),
            ('The Martian',
             'Andy Weir',
             445000,
             6,
             'A fast science-fiction survival story about an astronaut using engineering, humor, and persistence to '
             'stay alive on Mars.')]},
 {'name': '💻 برنامه\u200cنویسی و تکنولوژی',
  'slug': 'programming',
  'books': [('Python Crash Course',
             'Eric Matthes',
             620000,
             10,
             'A practical introduction to Python fundamentals followed by hands-on projects for building real '
             'programming confidence.'),
            ('Automate the Boring Stuff with Python',
             'Al Sweigart',
             540000,
             14,
             'A task-focused Python book covering useful automation for files, spreadsheets, web tasks, and everyday '
             'computer work.'),
            ('Clean Code',
             'Robert C. Martin',
             590000,
             8,
             'A software craftsmanship book focused on readable code, naming, functions, structure, and maintainable '
             'development habits.'),
            ('The Pragmatic Programmer',
             'Andrew Hunt & David Thomas',
             650000,
             5,
             'A broad software-development guide about problem solving, professional habits, maintainability, and '
             'practical engineering judgment.'),
            ('Grokking Algorithms',
             'Aditya Bhargava',
             510000,
             11,
             'A visual and approachable introduction to common algorithms, data structures, recursion, graphs, and '
             'algorithmic thinking.'),
            ('Designing Data-Intensive Applications',
             'Martin Kleppmann',
             790000,
             4,
             'A deeper systems book about data models, storage, replication, distributed systems, reliability, and '
             'scalability tradeoffs.')]},
 {'name': '🧠 روانشناسی و رشد فردی',
  'slug': 'psychology',
  'books': [('Atomic Habits',
             'James Clear',
             395000,
             20,
             'A practical framework for building better habits through small changes, environment design, consistency, '
             'and feedback.'),
            ('Thinking, Fast and Slow',
             'Daniel Kahneman',
             470000,
             8,
             'An exploration of intuitive and deliberate thinking, judgment, bias, risk, and how people make everyday '
             'decisions.'),
            ('Mindset',
             'Carol S. Dweck',
             355000,
             13,
             'A book about fixed and growth mindsets and how beliefs about ability can shape learning, resilience, and '
             'improvement.'),
            ('The Power of Habit',
             'Charles Duhigg',
             375000,
             9,
             'A look at how habits form, why routines persist, and how habit loops can be understood and changed.'),
            ('Deep Work',
             'Cal Newport',
             360000,
             15,
             'A productivity book about focused work, reducing distraction, and building the ability to concentrate on '
             'demanding tasks.'),
            ('Emotional Intelligence',
             'Daniel Goleman',
             430000,
             0,
             'An introduction to emotional awareness, self-regulation, empathy, motivation, and social skills in '
             'personal and professional life.')]},
 {'name': '💼 کسب\u200cوکار و مدیریت',
  'slug': 'business',
  'books': [('The Lean Startup',
             'Eric Ries',
             420000,
             10,
             'A startup framework centered on rapid experiments, validated learning, customer feedback, and reducing '
             'wasted effort.'),
            ('Start With Why',
             'Simon Sinek',
             390000,
             9,
             'A leadership and communication book about purpose, trust, motivation, and explaining why an organization '
             'exists.'),
            ('Zero to One',
             'Peter Thiel',
             410000,
             7,
             'A collection of ideas about startups, competition, innovation, differentiation, and building something '
             'meaningfully new.'),
            ('Rework',
             'Jason Fried & David Heinemeier Hansson',
             340000,
             12,
             'A concise collection of unconventional ideas about building products, running small teams, and avoiding '
             'unnecessary business complexity.'),
            ('The Psychology of Money',
             'Morgan Housel',
             380000,
             16,
             'A set of stories and lessons about behavior, uncertainty, wealth, risk, patience, and decision-making '
             'with money.'),
            ('Good to Great',
             'Jim Collins',
             450000,
             6,
             'A management study examining patterns associated with companies that improved performance and sustained '
             'stronger results.')]},
 {'name': '🏛 کلاسیک\u200cهای جهان',
  'slug': 'classics',
  'books': [('1984',
             'George Orwell',
             275000,
             18,
             'A dystopian novel about surveillance, propaganda, language, personal freedom, and life under an '
             'authoritarian state.'),
            ('Animal Farm',
             'George Orwell',
             235000,
             22,
             'A political allegory about power, revolution, leadership, and how ideals can be distorted over time.'),
            ('Pride and Prejudice',
             'Jane Austen',
             315000,
             10,
             'A classic novel of family, social expectations, first impressions, personal growth, and romantic '
             'misunderstanding.'),
            ('Crime and Punishment',
             'Fyodor Dostoevsky',
             520000,
             7,
             'A psychological classic exploring guilt, morality, isolation, consequence, and the inner conflict of a '
             'troubled student.'),
            ('The Great Gatsby',
             'F. Scott Fitzgerald',
             295000,
             11,
             'A classic American novel about ambition, wealth, longing, image, and the distance between dreams and '
             'reality.'),
            ('Jane Eyre',
             'Charlotte Bronte',
             360000,
             8,
             'A coming-of-age classic following an independent young woman through hardship, work, love, and moral '
             'choices.')]}]


async def seed_catalog(session: AsyncSession) -> bool:
    existing_count = await session.scalar(select(func.count(Category.id)))
    if existing_count and existing_count > 0:
        return False

    for category_data in BOOK_CATALOG:
        category = Category(name=category_data["name"], slug=category_data["slug"])
        session.add(category)
        await session.flush()

        for index, book in enumerate(category_data["books"], start=1):
            name, author, price, stock, description = book
            session.add(Product(
                category_id=category.id,
                name=name,
                author=author,
                price=price,
                stock=stock,
                description=description,
                image_path=f"assets/covers/{category_data['slug']}_{index:02d}.png",
            ))

    await session.commit()
    return True
