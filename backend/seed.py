from app.database import Base, engine, SessionLocal
from app.models import Student, Course, Prerequisite
Base.metadata.create_all(bind=engine)
db=SessionLocal()
catalog=[
 ("CS101","Python Programming",4,1,"Core",["programming","ai"],2), ("MA101","Linear Algebra",4,1,"Mathematics",["ai","machine learning"],3),
 ("CS201","Data Structures",4,2,"Core",["programming","software"],3), ("ST201","Probability and Statistics",3,2,"Mathematics",["data","machine learning"],3),
 ("CS202","Database Systems",3,3,"Core",["data","software"],3), ("CS301","Algorithms",4,3,"Core",["programming","software"],4),
 ("AI301","Machine Learning",4,4,"AI",["ai","machine learning","data"],4), ("AI302","Natural Language Processing",3,5,"AI",["ai","nlp","machine learning"],4),
 ("AI303","Computer Vision",3,5,"AI",["ai","machine learning"],4), ("AI401","Deep Learning",4,6,"AI",["ai","machine learning"],5),
 ("AI402","Generative AI",3,7,"AI",["ai","nlp","machine learning"],5), ("AI403","Reinforcement Learning",3,7,"AI",["ai","machine learning"],5),
 ("CS402","Cloud Computing",3,6,"Elective",["software","data"],3), ("CS403","Responsible AI",2,6,"Elective",["ai","ethics"],2),
 ("AI404","Capstone: Advising Systems",4,8,"Project",["ai","software"],5)]
for row in catalog:
 code,name,credits,sem,cat,tags,diff=row
 course=db.get(Course,code) or Course(code=code)
 course.name=name; course.credits=credits; course.semester=sem; course.category=cat; course.interest_tags=tags; course.difficulty=diff; course.availability=True
 db.add(course)
edges=[("CS101","CS201"),("CS201","CS301"),("CS101","AI301"),("MA101","AI301"),("ST201","AI301"),("AI301","AI302"),("AI301","AI303"),("AI301","AI401"),("CS201","AI401"),("AI401","AI402"),("AI302","AI402"),("AI401","AI403"),("CS202","CS402"),("AI301","CS403"),("AI402","AI404"),("CS301","AI404")]
for a,b in edges:
 if not db.query(Prerequisite).filter_by(course_code=b,prerequisite_code=a).first(): db.add(Prerequisite(course_code=b,prerequisite_code=a))
student=db.query(Student).filter_by(student_id="20231CAI0155").first()
profile={"name":"Prabuddha P","current_semester":5,"completed_credits":66,"interests":["AI","Machine Learning","NLP","Data"],"career_goal":"AI/ML Engineer","gpa":3.6,"max_credits":18,"completed_courses":["CS101","MA101","CS201","ST201","CS202","CS301"]}
if student is None: student=Student(student_id="20231CAI0155",**profile)
else:
 student.interest_rows.clear(); student.completed_course_rows.clear(); db.flush()
 for key,value in profile.items(): setattr(student,key,value)
db.add(student)
db.commit(); db.close(); print("Seeded 1 demo student, 15 courses, and 16 prerequisite links.")
