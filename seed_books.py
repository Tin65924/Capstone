"""
Book Data Seeder — MCST LMS (Capstone).

Populates realistic book data for 9 academic programs with >= 5,000
physical copies. Follows the existing schema exactly (no schema changes):

  * book_catalog ... one row per unique TITLE (title + author NOT NULL,
    no program/author/publisher tables exist, no quantity column).
  * accession_log ... one row per PHYSICAL COPY (accession_number UNIQUE
    NOT NULL, book_id FK, librarian_id FK -> user_accounts NOT NULL).
  * departments ..... the 9 programs are registered here
    (dept_type='program'); each title's subject_classification carries
    its subject and its description names its program, since book_catalog
    has no program column.

Conventions (per AGENTS.md): raw psycopg2, %s placeholders, no ORM.

Usage — local dev (uses DATABASE_URL from .env):
    venv\\Scripts\\python.exe seed_books.py

Usage — prod (Neon): pass the connection string with --dsn so your local
.env stays untouched. Neon requires SSL, so keep ?sslmode=require
(which Neon already appends to the URL it shows you):
    venv\\Scripts\\python.exe seed_books.py --dsn "postgresql://<user>:<pw>@<host>.neon.tech/<db>?sslmode=require"

    venv\\Scripts\\python.exe seed_books.py --dsn "..." --reset   # wipe prior seeded rows first
    venv\\Scripts\\python.exe seed_books.py --dsn "..." --target 5500
    venv\\Scripts\\python.exe seed_books.py --prefix BKSEED-      # old prefixed numbering

Accession numbers are plain zero-padded sequences: 0001, 0002, ...
On a fresh database the seeded copies become 0001..NNNN with no gaps.
On a rerun, books that already have their planned copies are skipped and
any missing copies continue from max(existing)+1, so numbering is never
reused and no duplicates are created.

Idempotent / safely rerunnable:
  * Books are matched on their natural key (title, author, isbn) —
    existing titles are reused, never duplicated.
  * Seeded books carry a [SEED-BOOKS] marker in their description; reruns
    count each seeded book's existing copies and only top up the shortfall
    (same no-duplicate principle as the bulk-import worker in
    app/cataloging/routes.py).
  * --reset removes ONLY rows created by this seeder (accessions belonging
    to [SEED-BOOKS] titles, plus their dependent circulation/inventory rows
    and catalog rows left with no copies), never user data.
"""

import argparse
import os
import re
import sys

SEED_MARKER = "[SEED-BOOKS]"
SEED_LIBRARIAN_EMAIL = "seed-books@mcst.edu.ph"
TARGET_COPIES = 5100  # >= 5,000 required; slight headroom for safety

PROGRAMS = [
    "Bachelor of Arts in Communication",
    "BS Information Systems",
    "BS Mathematics",
    "BS Nursing",
    "Bachelor of Physical Education",
    "Bachelor of Public Administration",
    "BS Criminology",
    "Early Childhood Education",
    "Special Needs Education",
]

# (title, author, edition, publisher, year, subject, copies, blurb)
# Core textbooks carry many copies; supplementary titles fewer; a few
# single-copy references. All titles are real, well-known books relevant
# to their program.
BOOKS = {
    # ---------------------------------------------------------------- BACOMM
    "Bachelor of Arts in Communication": [
        ("McQuail's Mass Communication Theory", "Denis McQuail and Mark Deuze", "7th", "SAGE Publications", 2020, "Media Theory", 20, "Foundational theory of mass communication and media effects."),
        ("Understanding Media: The Extensions of Man", "Marshall McLuhan", "Reprint", "MIT Press", 1994, "Media Theory", 12, "Classic study of media as extensions of human senses."),
        ("Mass Communication: Living in a Media World", "Ralph E. Hanson", "8th", "SAGE Publications", 2021, "Mass Communication", 18, "Introductory survey of mass media industries and issues."),
        ("Media Literacy", "W. James Potter", "10th", "SAGE Publications", 2021, "Media Literacy", 15, "Framework for critically analyzing media messages."),
        ("The Elements of Journalism", "Bill Kovach and Tom Rosenstiel", "4th", "Crown", 2021, "Journalism", 18, "Core principles and purpose of journalism."),
        ("Writing for the Mass Media", "James G. Stovall", "10th", "Pearson", 2018, "Media Writing", 15, "Practical guide to news, PR, and broadcast writing."),
        ("The Associated Press Stylebook", "Associated Press", "57th", "Basic Books", 2024, "Journalism", 12, "Standard style and usage guide for journalists."),
        ("Public Relations: Strategies and Tactics", "Dennis L. Wilcox and Glen T. Cameron", "12th", "Pearson", 2020, "Public Relations", 16, "Comprehensive introduction to PR planning and practice."),
        ("Advertising: Principles and Practice", "Sandra Moriarty, Nancy Mitchell, and William Wells", "11th", "Pearson", 2021, "Advertising", 14, "Principles of advertising strategy and creative execution."),
        ("Broadcast News Writing, Style, and Reporting", "Ted White and Frank Barnas", "5th", "Routledge", 2012, "Broadcast Journalism", 12, "Writing and producing news for radio and television."),
        ("Media Ethics: Cases and Moral Reasoning", "Clifford G. Christians, Mark Fackler, and Kathy Brittain Richardson", "11th", "Routledge", 2020, "Media Ethics", 12, "Case-based approach to ethical decision-making in media."),
        ("An Introduction to Visual Communication", "Susan Barnes", "3rd", "Peter Lang", 2017, "Visual Communication", 8, "How images communicate meaning across media."),
        ("Film Art: An Introduction", "David Bordwell, Kristin Thompson, and Jeff Smith", "13th", "McGraw-Hill", 2023, "Film Studies", 14, "Formal analysis of film style and narration."),
        ("Convergence Culture", "Henry Jenkins", "Reprint", "NYU Press", 2008, "New Media", 8, "Where old and new media collide in participatory culture."),
        ("The Medium Is the Massage", "Marshall McLuhan and Quentin Fiore", "Reprint", "Gingko Press", 2001, "Media Theory", 6, "Illustrated exploration of media effects."),
        ("Manufacturing Consent", "Edward S. Herman and Noam Chomsky", "Reprint", "Pantheon", 2002, "Media Criticism", 8, "Propaganda model of mass media in democracies."),
        ("Amusing Ourselves to Death", "Neil Postman", "Reprint", "Penguin", 2005, "Media Criticism", 8, "Public discourse in the age of show business."),
        ("Public Opinion", "Walter Lippmann", "Reprint", "Free Press", 1997, "Media Theory", 5, "Classic on public opinion and the press."),
        ("Theories of Human Communication", "Stephen W. Littlejohn, Karen A. Foss, and John G. Oetzel", "12th", "Waveland Press", 2021, "Communication Theory", 14, "Survey of major human communication theories."),
        ("Interpersonal Communication: Everyday Encounters", "Julia T. Wood", "9th", "Cengage", 2019, "Interpersonal Communication", 10, "Applying interpersonal theory to daily interaction."),
        ("Organizational Communication: Approaches and Processes", "Katherine Miller", "8th", "Cengage", 2021, "Organizational Communication", 10, "Classical to critical approaches in organizations."),
        ("Intercultural Communication in Contexts", "Judith N. Martin and Thomas K. Nakayama", "8th", "McGraw-Hill", 2021, "Intercultural Communication", 10, "Culture, power, and communication across contexts."),
        ("Strategic Writing: Multimedia Writing for Public Relations, Advertising, and More", "Charles Marsh, David Guth, and Bonnie Poovey Short", "5th", "Routledge", 2021, "Public Relations", 8, "Strategic message design across media platforms."),
        ("Photojournalism: The Professional's Approach", "Kenneth Kobre", "7th", "Routledge", 2017, "Photojournalism", 6, "Technique and storytelling in news photography."),
        ("Sound Reporting: The NPR Guide to Audio Journalism", "Jonathan Kern", "2nd", "University of Chicago Press", 2012, "Broadcast Journalism", 6, "Field guide to audio journalism and podcasting."),
        ("The Art of the Documentary", "Megan Cunningham", "2nd", "New Riders", 2014, "Film Studies", 5, "Craft of documentary filmmaking from idea to screen."),
        ("Development Communication: Theory and Practice", "Nora C. Quebral", "2nd", "University of the Philippines Press", 2012, "Development Communication", 12, "Seminal Filipino text on communication for development."),
        ("Philippine Communication Today", "Crispin C. Maslog", "2nd", "Philippine Association of Communication Educators", 2007, "Philippine Media", 10, "Overview of the Philippine communication landscape."),
        ("Media and Society in the Philippines", "Elizabeth L. Enriquez", "1st", "University of the Philippines Press", 2008, "Philippine Media", 8, "Broadcast media history and society in the Philippines."),
        ("Digital Media Ethics", "Charles Ess", "3rd", "Polity", 2020, "New Media", 6, "Ethics of online communication and digital life."),
        ("Social Media: A Critical Introduction", "Christian Fuchs", "4th", "SAGE Publications", 2024, "New Media", 8, "Critical theory of social media platforms."),
        ("The Newsroom: A Practical Guide", "Melanie Moreno", "1st", "Anvil Publishing", 2016, "Journalism", 5, "Newsroom workflows for student journalists."),
        ("Feature Writing: A Practical Introduction", "Susan Pape and Sue Featherstone", "2nd", "SAGE Publications", 2018, "Media Writing", 6, "Craft of writing features and human-interest stories."),
        ("Speech Communication Made Simple", "Mylene C. Quinto", "3rd", "C and E Publishing", 2019, "Speech Communication", 10, "Public speaking fundamentals for Filipino students."),
        ("Argumentation and Debate", "Austin J. Freeley and David L. Steinberg", "13th", "Cengage", 2013, "Speech Communication", 6, "Reasoning, briefing, and competitive debate."),
        ("The Business of Media", "David Croteau and William Hoynes", "4th", "SAGE Publications", 2022, "Media Industries", 6, "Ownership, economics, and power in media industries."),
        ("Community Radio in the Philippines", "Louie Tabing", "1st", "Tambuli Foundation", 2010, "Philippine Media", 4, "Practice of community broadcasting in the Philippines."),
        ("Media Research Methods", "Anders Hansen and David Machin", "2nd", "Bloomsbury", 2019, "Communication Research", 8, "Methods for studying media content and audiences."),
        ("Communication Research: Asking Questions, Finding Answers", "Joann Keyton", "5th", "McGraw-Hill", 2018, "Communication Research", 8, "Designing and conducting communication studies."),
        ("Crisis Communication: Theory and Practice", "W. Timothy Coombs", "2nd", "SAGE Publications", 2022, "Public Relations", 6, "Managing organizational crises through communication."),
        ("The Copywriter's Handbook", "Robert W. Bly", "4th", "Holt", 2020, "Advertising", 5, "Writing copy that sells across media."),
        ("Documentary Storytelling", "Sheila Curran Bernard", "5th", "Routledge", 2022, "Film Studies", 4, "Story craft for nonfiction film and video."),
        ("Mobile Journalism", "Marc Blank-Settle", "1st", "Routledge", 2019, "Broadcast Journalism", 4, "Reporting and storytelling with a smartphone."),
        ("Online Journalism: Principles and Practices", "Randall S. Sumpter and James W. Tankard", "3rd", "Routledge", 2016, "New Media", 5, "Reporting and ethics for the web."),
        ("Theories of the Information Society", "Frank Webster", "4th", "Routledge", 2014, "Media Theory", 4, "Leading theories of the information age."),
        ("Rhetoric: A Very Short Introduction", "Richard Toye", "1st", "Oxford University Press", 2013, "Speech Communication", 3, "Concise history and theory of rhetoric."),
        ("Philippine Cinema: A History", "Nick Deocampo", "1st", "Anvil Publishing", 2011, "Film Studies", 5, "History of film as art and industry in the Philippines."),
        ("Media Law in the Philippines", "Luis V. Teodoro", "1st", "University of the Philippines Press", 2015, "Media Law", 6, "Libel, press freedom, and broadcast regulation locally."),
        ("Freedom of Expression and the Press", "Raul C. Pangalangan", "1st", "University of the Philippines Law Center", 2009, "Media Law", 3, "Constitutional foundations of press freedom."),
        ("Podcasting: A Practical Guide", "Mia Lobel", "1st", "Routledge", 2021, "Broadcast Journalism", 1, "Launching and producing narrative podcasts."),
    ],
    # ------------------------------------------------------------------ BSIS
    "BS Information Systems": [
        ("Introduction to Algorithms", "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein", "4th", "MIT Press", 2022, "Algorithms", 20, "Definitive textbook on algorithms and data structures."),
        ("Clean Code: A Handbook of Agile Software Craftsmanship", "Robert C. Martin", "1st", "Prentice Hall", 2008, "Software Engineering", 18, "Principles and practices of readable, maintainable code."),
        ("The Pragmatic Programmer", "David Thomas and Andrew Hunt", "2nd", "Addison-Wesley", 2019, "Software Engineering", 15, "Timeless practical advice for software developers."),
        ("Design Patterns: Elements of Reusable Object-Oriented Software", "Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides", "1st", "Addison-Wesley", 1994, "Software Engineering", 15, "Classic catalog of object-oriented design patterns."),
        ("Database System Concepts", "Abraham Silberschatz, Henry F. Korth, and S. Sudarshan", "7th", "McGraw-Hill", 2019, "Databases", 20, "Fundamentals of database design and systems."),
        ("Fundamentals of Database Systems", "Ramez Elmasri and Shamkant B. Navathe", "7th", "Pearson", 2015, "Databases", 16, "Data modeling, SQL, and database theory."),
        ("Operating System Concepts", "Abraham Silberschatz, Peter B. Galvin, and Greg Gagne", "10th", "Wiley", 2021, "Operating Systems", 16, "Processes, memory, storage, and concurrency."),
        ("Computer Networking: A Top-Down Approach", "James F. Kurose and Keith W. Ross", "8th", "Pearson", 2021, "Networking", 16, "Internet architecture from applications downward."),
        ("Artificial Intelligence: A Modern Approach", "Stuart Russell and Peter Norvig", "4th", "Pearson", 2020, "Artificial Intelligence", 14, "Comprehensive introduction to AI theory and methods."),
        ("Software Engineering", "Ian Sommerville", "10th", "Pearson", 2015, "Software Engineering", 16, "Plan-driven and agile software engineering practice."),
        ("Systems Analysis and Design", "Kenneth E. Kendall and Julie E. Kendall", "11th", "Pearson", 2019, "Systems Analysis and Design", 18, "Methods for analyzing and designing information systems."),
        ("Modern Systems Analysis and Design", "Joseph S. Valacich and Joey F. George", "9th", "Pearson", 2020, "Systems Analysis and Design", 14, "Object-oriented systems development with UML."),
        ("Management Information Systems: Managing the Digital Firm", "Kenneth C. Laudon and Jane P. Laudon", "17th", "Pearson", 2023, "Information Systems", 16, "Business value of enterprise information systems."),
        ("Information Technology Project Management", "Kathy Schwalbe", "9th", "Cengage", 2018, "Project Management", 14, "Managing IT projects through the PMBOK lens."),
        ("A Guide to the Project Management Body of Knowledge (PMBOK Guide)", "Project Management Institute", "7th", "Project Management Institute", 2021, "Project Management", 10, "Global standard for project management practice."),
        ("Computer Organization and Design", "David A. Patterson and John L. Hennessy", "6th", "Morgan Kaufmann", 2020, "Computer Architecture", 10, "Hardware-software interface in RISC-V and MIPS."),
        ("Discrete Mathematics and Its Applications", "Kenneth H. Rosen", "8th", "McGraw-Hill", 2019, "Discrete Mathematics", 12, "Logic, proofs, combinatorics, and graphs for computing."),
        ("Python Crash Course", "Eric Matthes", "3rd", "No Starch Press", 2023, "Programming", 14, "Hands-on project-based introduction to Python."),
        ("Java: How to Program", "Paul Deitel and Harvey Deitel", "11th", "Pearson", 2017, "Programming", 12, "Java programming from basics to GUIs and web services."),
        ("Web Programming Step by Step", "Marty Stepp, Jessica Miller, and Victoria Kirst", "2nd", "Lulu Press", 2012, "Web Development", 8, "HTML, CSS, JavaScript, and PHP for beginners."),
        ("Learning Web Design", "Jennifer Robbins", "5th", "O'Reilly Media", 2018, "Web Development", 10, "Beginner's guide to HTML, CSS, JavaScript, and graphics."),
        ("Eloquent JavaScript", "Marijn Haverbeke", "4th", "No Starch Press", 2024, "Web Development", 8, "Modern introduction to JavaScript programming."),
        ("PHP and MySQL Web Development", "Luke Welling and Laura Thomson", "5th", "Addison-Wesley", 2016, "Web Development", 10, "Building database-driven websites with PHP and MySQL."),
        ("Data Mining: Concepts and Techniques", "Jiawei Han, Micheline Kamber, and Jian Pei", "4th", "Morgan Kaufmann", 2022, "Data Science", 10, "Methods for mining large datasets."),
        ("Python for Data Analysis", "Wes McKinney", "3rd", "O'Reilly Media", 2022, "Data Science", 10, "Data wrangling with pandas, NumPy, and Jupyter."),
        ("Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow", "Aurelien Geron", "3rd", "O'Reilly Media", 2022, "Machine Learning", 10, "Practical ML systems with Python frameworks."),
        ("Information Security: Principles and Practice", "Mark Stamp", "2nd", "Wiley", 2011, "Information Security", 10, "Access control, crypto, and software security."),
        ("Principles of Information Security", "Michael E. Whitman and Herbert J. Mattord", "7th", "Cengage", 2021, "Information Security", 12, "Managerial and technical foundations of infosec."),
        ("CompTIA Security+ Guide to Network Security Fundamentals", "Mark Ciampa", "7th", "Cengage", 2021, "Information Security", 8, "Exam-aligned guide to network defense."),
        ("Computer Networks", "Andrew S. Tanenbaum, Nick Feamster, and David J. Wetherall", "6th", "Pearson", 2021, "Networking", 10, "Layered reference on network protocols and design."),
        ("Cloud Computing: Concepts, Technology and Architecture", "Thomas Erl, Ricardo Puttini, and Zaigham Mahmood", "2nd", "Prentice Hall", 2023, "Cloud Computing", 8, "Cloud models, mechanisms, and architectures."),
        ("Enterprise Architecture as Strategy", "Jeanne W. Ross, Peter Weill, and David C. Robertson", "1st", "Harvard Business Review Press", 2006, "Enterprise Architecture", 6, "Building operating models on enterprise IT foundations."),
        ("IT Governance: How Top Performers Manage IT Decision Rights", "Peter Weill and Jeanne W. Ross", "1st", "Harvard Business School Press", 2004, "IT Governance", 5, "Frameworks for governing enterprise IT."),
        ("Human-Computer Interaction", "Alan Dix, Janet Finlay, Gregory Abowd, and Russell Beale", "3rd", "Pearson", 2003, "Human-Computer Interaction", 8, "Designing usable interactive systems."),
        ("Don't Make Me Think", "Steve Krug", "Revisited", "New Riders", 2014, "Human-Computer Interaction", 8, "Common-sense approach to web usability."),
        ("The Design of Everyday Things", "Don Norman", "Revised", "Basic Books", 2013, "Human-Computer Interaction", 10, "Human-centered design of objects and interfaces."),
        ("Agile Software Development with Scrum", "Ken Schwaber and Mike Beadle", "1st", "Prentice Hall", 2001, "Software Engineering", 6, "Foundational guide to the Scrum framework."),
        ("User Stories Applied", "Mike Cohn", "1st", "Addison-Wesley", 2004, "Software Engineering", 5, "Agile requirements through user stories."),
        ("Head First Design Patterns", "Eric Freeman and Elisabeth Robson", "2nd", "O'Reilly Media", 2020, "Software Engineering", 10, "Brain-friendly tour of design patterns."),
        ("Structure and Interpretation of Computer Programs", "Harold Abelson and Gerald Jay Sussman", "2nd", "MIT Press", 1996, "Programming", 6, "Foundational CS text using Scheme."),
        ("The C Programming Language", "Brian W. Kernighan and Dennis M. Ritchie", "2nd", "Prentice Hall", 1988, "Programming", 6, "Classic reference for the C language."),
        ("Introduction to the Theory of Computation", "Michael Sipser", "3rd", "Cengage", 2012, "Theory of Computing", 6, "Automata, computability, and complexity."),
        ("Data and Computer Communications", "William Stallings", "10th", "Pearson", 2017, "Networking", 8, "Transmission media, protocols, and architectures."),
        ("Business Process Management", "John Jeston", "4th", "Routledge", 2018, "Information Systems", 5, "Practical BPM framework for enterprises."),
        ("E-Commerce: Business, Technology, Society", "Kenneth C. Laudon and Carol Guercio Traver", "16th", "Pearson", 2020, "E-Commerce", 8, "Online business models and technologies."),
        ("Accounting Information Systems", "Marshall B. Romney and Paul John Steinbart", "15th", "Pearson", 2023, "Information Systems", 6, "Controls and processes in AIS."),
        ("Systems Architecture", "Stephen D. Burd", "7th", "Cengage", 2020, "Computer Architecture", 5, "Hardware, software, and enterprise architecture."),
        ("Ethics in Information Technology", "George W. Reynolds", "6th", "Cengage", 2018, "IT Ethics", 8, "Privacy, crime, and professional ethics in IT."),
        ("IT Auditing: Using Controls to Protect Information Assets", "Chris Davis, Mike Schiller, and Kevin Wheeler", "2nd", "McGraw-Hill", 2011, "IT Governance", 4, "Audit and control of information systems."),
        ("Data Science for Business", "Foster Provost and Tom Fawcett", "1st", "O'Reilly Media", 2013, "Data Science", 1, "Data-analytic thinking for business decisions."),
    ],
    # ------------------------------------------------------------------ MATH
    "BS Mathematics": [
        ("Calculus: Early Transcendentals", "James Stewart, Daniel K. Clegg, and Saleem Watson", "9th", "Cengage", 2020, "Calculus", 20, "Standard single- and multivariable calculus text."),
        ("Thomas' Calculus", "George B. Thomas, Maurice D. Weir, and Joel R. Hass", "15th", "Pearson", 2023, "Calculus", 18, "Comprehensive calculus with applications."),
        ("Elementary Linear Algebra", "Howard Anton and Chris Rorres", "11th", "Wiley", 2013, "Linear Algebra", 16, "Vectors, matrices, and linear transformations."),
        ("Linear Algebra Done Right", "Sheldon Axler", "4th", "Springer", 2024, "Linear Algebra", 10, "Determinant-free development of linear algebra."),
        ("Discrete Mathematics and Its Applications", "Kenneth H. Rosen", "8th", "McGraw-Hill", 2019, "Discrete Mathematics", 16, "Logic, counting, relations, and graph theory."),
        ("Discrete Mathematics with Applications", "Susanna S. Epp", "5th", "Cengage", 2019, "Discrete Mathematics", 12, "Reasoning-focused discrete mathematics."),
        ("How to Prove It: A Structured Approach", "Daniel J. Velleman", "3rd", "Cambridge University Press", 2019, "Mathematical Proof", 12, "Step-by-step guide to constructing proofs."),
        ("Abstract Algebra", "David S. Dummit and Richard M. Foote", "3rd", "Wiley", 2003, "Abstract Algebra", 14, "Groups, rings, and fields with depth."),
        ("A First Course in Abstract Algebra", "John B. Fraleigh", "8th", "Pearson", 2020, "Abstract Algebra", 12, "Accessible entry to groups, rings, and fields."),
        ("Contemporary Abstract Algebra", "Joseph A. Gallian", "10th", "CRC Press", 2021, "Abstract Algebra", 10, "Student-friendly algebra with applications."),
        ("Elementary Analysis: The Theory of Calculus", "Kenneth A. Ross", "2nd", "Springer", 2013, "Real Analysis", 12, "Rigorous foundations of single-variable analysis."),
        ("Understanding Analysis", "Stephen Abbott", "2nd", "Springer", 2015, "Real Analysis", 10, "Motivated introduction to real analysis."),
        ("Principles of Mathematical Analysis", "Walter Rudin", "3rd", "McGraw-Hill", 1976, "Real Analysis", 8, "Classic rigorous analysis text."),
        ("Complex Variables and Applications", "James Ward Brown and Ruel V. Churchill", "9th", "McGraw-Hill", 2013, "Complex Analysis", 10, "Analytic functions, residues, and mappings."),
        ("Elementary Differential Equations and Boundary Value Problems", "William E. Boyce, Richard C. DiPrima, and Douglas B. Meade", "12th", "Wiley", 2021, "Differential Equations", 14, "ODEs, systems, and boundary value problems."),
        ("Differential Equations with Applications", "Dennis G. Zill", "11th", "Cengage", 2024, "Differential Equations", 12, "Applied first course in differential equations."),
        ("Probability and Statistics", "Morris H. DeGroot and Mark J. Schervish", "4th", "Pearson", 2011, "Probability", 12, "Calculus-based probability and inference."),
        ("Mathematical Statistics with Applications", "Dennis D. Wackerly, William Mendenhall, and Richard L. Scheaffer", "7th", "Cengage", 2007, "Statistics", 14, "Applied statistical inference with theory."),
        ("Introductory Statistics", "Neil A. Weiss", "10th", "Pearson", 2020, "Statistics", 10, "Descriptive and inferential statistics."),
        ("Introduction to Probability Models", "Sheldon M. Ross", "13th", "Academic Press", 2023, "Probability", 8, "Stochastic models across disciplines."),
        ("Numerical Analysis", "Richard L. Burden, J. Douglas Faires, and Annette M. Burden", "10th", "Cengage", 2015, "Numerical Analysis", 10, "Algorithms for scientific computation."),
        ("Operations Research: An Introduction", "Hamdy A. Taha", "10th", "Pearson", 2017, "Operations Research", 10, "Linear programming, queues, and simulation."),
        ("Introduction to Operations Research", "Frederick S. Hillier and Gerald J. Lieberman", "11th", "McGraw-Hill", 2021, "Operations Research", 8, "Optimization models and methods."),
        ("Topology", "James R. Munkres", "2nd", "Pearson", 2013, "Topology", 6, "Point-set and algebraic topology foundations."),
        ("Elementary Number Theory", "David M. Burton", "8th", "McGraw-Hill", 2024, "Number Theory", 8, "Divisibility, congruences, and Diophantine equations."),
        ("An Introduction to the Theory of Numbers", "G. H. Hardy and E. M. Wright", "6th", "Oxford University Press", 2008, "Number Theory", 5, "Classic exposition of number theory."),
        ("History of Mathematics", "Victor J. Katz", "3rd", "Pearson", 2008, "History of Mathematics", 8, "Development of mathematics across cultures."),
        ("Mathematics for Elementary Teachers", "Tom Bassarear and Meg Moss", "6th", "Cengage", 2019, "Mathematics Education", 10, "Content knowledge for teaching K-6 mathematics."),
        ("Teaching Secondary Mathematics", "David Rock and Douglas K. Brumbaugh", "5th", "Routledge", 2018, "Mathematics Education", 8, "Methods for the high-school mathematics classroom."),
        ("College Geometry", "David C. Kay", "2nd", "Pearson", 2011, "Geometry", 8, "Euclidean and transformational geometry."),
        ("Geometry: A High School Course", "Serge Lang and Gene Murrow", "2nd", "Springer", 1988, "Geometry", 6, "Rigorous high-school geometry."),
        ("Linear Programming and Network Flows", "Mokhtar S. Bazaraa, John J. Jarvis, and Hanif D. Sherali", "4th", "Wiley", 2009, "Operations Research", 5, "Theory and algorithms of linear optimization."),
        ("Mathematical Modeling", "Mark M. Meerschaert", "4th", "Academic Press", 2013, "Mathematical Modeling", 6, "Building models with difference and differential equations."),
        ("A First Course in Probability", "Sheldon M. Ross", "10th", "Pearson", 2019, "Probability", 8, "Undergraduate introduction to probability theory."),
        ("Statistics for Engineers and Scientists", "William Navidi", "5th", "McGraw-Hill", 2019, "Statistics", 8, "Statistics with engineering applications."),
        ("Mathematics of Finance", "Petr Zima and Robert L. Brown", "2nd", "McGraw-Hill", 2011, "Financial Mathematics", 6, "Interest, annuities, and investment mathematics."),
        ("An Introduction to Actuarial Mathematics", "Arjun K. Gupta and Tamas Varga", "1st", "Springer", 2013, "Actuarial Science", 4, "Risk, survival models, and life contingencies."),
        ("Graph Theory with Applications to Engineering and Computer Science", "Narsingh Deo", "Reprint", "Dover", 2016, "Graph Theory", 5, "Graphs, trees, and networks for applications."),
        ("Introduction to Graph Theory", "Douglas B. West", "2nd", "Pearson", 2000, "Graph Theory", 5, "Core theorems and proofs in graph theory."),
        ("Set Theory and Logic", "Robert R. Stoll", "Reprint", "Dover", 1979, "Foundations", 4, "Sets, relations, and formal logic."),
        ("Godel, Escher, Bach", "Douglas R. Hofstadter", "20th Anniversary", "Basic Books", 1999, "Foundations", 4, "Minds, machines, and mathematical meaning."),
        ("Fermat's Last Theorem", "Simon Singh", "Reprint", "Anchor", 1998, "History of Mathematics", 4, "Story of the famous conjecture and its proof."),
        ("The Man Who Knew Infinity", "Robert Kanigel", "Reprint", "Washington Square Press", 2015, "History of Mathematics", 3, "Life of mathematician Srinivasa Ramanujan."),
        ("Problem Solving Through Recreational Mathematics", "Bonnie Averbach and Orin Chein", "Reprint", "Dover", 1999, "Problem Solving", 5, "Puzzles and games that teach mathematics."),
        ("Trigonometry", "Margaret L. Lial, John Hornsby, and David I. Schneider", "11th", "Pearson", 2016, "Trigonometry", 8, "Functions, identities, and applications."),
        ("College Algebra", "Robert F. Blitzer", "8th", "Pearson", 2021, "Algebra", 10, "Functions and modeling for college students."),
        ("Precalculus", "James Stewart, Lothar Redlin, and Saleem Watson", "7th", "Cengage", 2015, "Precalculus", 8, "Preparation for calculus with applications."),
        ("Math in Focus: Singapore Math", "Marshall Cavendish Education", "5th", "Marshall Cavendish", 2020, "Mathematics Education", 1, "Bar-model approach to school mathematics."),
    ],
    # ---------------------------------------------------------------- NURSING
    "BS Nursing": [
        ("Fundamentals of Nursing: The Art and Science of Person-Centered Care", "Carol R. Taylor, Pamela Lynn, and Jennifer L. Bartlett", "10th", "Wolters Kluwer", 2022, "Fundamentals of Nursing", 20, "Core concepts, skills, and clinical reasoning."),
        ("Kozier and Erb's Fundamentals of Nursing", "Audrey T. Berman, Shirlee Snyder, and Geralyn Frandsen", "11th", "Pearson", 2021, "Fundamentals of Nursing", 18, "Concepts, process, and practice of nursing."),
        ("Medical-Surgical Nursing: Assessment and Management of Clinical Problems", "Sharon L. Lewis, Linda Bucher, Margaret M. Heitkemper, and Mariann M. Harding", "11th", "Elsevier", 2019, "Medical-Surgical Nursing", 20, "Authoritative med-surg reference for students."),
        ("Brunner and Suddarth's Textbook of Medical-Surgical Nursing", "Janice L. Hinkle, Kerry H. Cheever, and Kristen J. Overbaugh", "15th", "Wolters Kluwer", 2021, "Medical-Surgical Nursing", 18, "Evidence-based adult health nursing."),
        ("Maternal Child Nursing Care", "Shannon E. Perry, Marilyn J. Hockenberry, and Deitra Leonard Lowdermilk", "7th", "Elsevier", 2022, "Maternal and Child Nursing", 16, "Care of mothers, newborns, and children."),
        ("Pediatric Nursing: The Critical Components of Nursing Care", "Kathryn Rudd and Diane M. Kocisko", "2nd", "F. A. Davis", 2018, "Pediatric Nursing", 14, "Growth, development, and child health nursing."),
        ("Psychiatric-Mental Health Nursing", "Sheila L. Videbeck", "9th", "Wolters Kluwer", 2022, "Psychiatric Nursing", 14, "Therapeutic communication and mental health care."),
        ("Community and Public Health Nursing", "Judith Allender, Cherie Rector, and Kristine Warner", "10th", "Wolters Kluwer", 2023, "Community Health Nursing", 16, "Population-focused nursing practice."),
        ("Public Health Nursing: Population-Centered Health Care", "Marcia Stanhope and Jeanette Lancaster", "11th", "Elsevier", 2023, "Community Health Nursing", 12, "Community assessment and program planning."),
        ("Health Assessment in Nursing", "Janet R. Weber and Jane H. Kelley", "7th", "Wolters Kluwer", 2021, "Health Assessment", 16, "Systematic physical examination skills."),
        ("Physical Examination and Health Assessment", "Carolyn Jarvis and Ann Eckhardt", "9th", "Elsevier", 2023, "Health Assessment", 14, "Evidence-based examination techniques."),
        ("Pharmacology and the Nursing Process", "Linda Lane Lilley, Shelly Rainforth Collins, and Julie S. Snyder", "10th", "Elsevier", 2022, "Pharmacology", 18, "Drug therapy integrated with the nursing process."),
        ("Lehne's Pharmacology for Nursing Care", "Jacqueline Burchum and Laura Rosenthal", "11th", "Elsevier", 2021, "Pharmacology", 14, "Prototype-based pharmacology for nurses."),
        ("Anatomy and Physiology for Nurses", "Inderbir Singh", "5th", "Jaypee Brothers", 2021, "Anatomy and Physiology", 16, "Body systems with clinical correlations."),
        ("Human Anatomy and Physiology", "Elaine N. Marieb and Katja Hoehn", "11th", "Pearson", 2018, "Anatomy and Physiology", 14, "Illustrated two-semester A and P course text."),
        ("Microbiology for the Healthcare Professional", "Karin C. VanMeter and Robert J. Hubert", "3rd", "Elsevier", 2021, "Microbiology", 12, "Pathogens and infection control for clinicians."),
        ("Biochemistry for Nurses", "Arvind S. Yadav", "2nd", "Jaypee Brothers", 2019, "Biochemistry", 10, "Metabolic pathways with nursing relevance."),
        ("Nutrition Essentials for Nursing Practice", "Susan G. Dudek", "9th", "Wolters Kluwer", 2021, "Nutrition", 12, "Nutrition across the lifespan and in illness."),
        ("Nursing Research: Generating and Assessing Evidence", "Denise F. Polit and Cheryl Tatano Beck", "11th", "Wolters Kluwer", 2020, "Nursing Research", 12, "Reading, using, and conducting nursing research."),
        ("Leadership and Nursing Care Management", "Diane L. Huber and Maria Lindell Joseph", "7th", "Elsevier", 2021, "Nursing Leadership", 12, "Management and leadership in nursing services."),
        ("Nursing Leadership and Management", "Patricia S. Yoder-Wise and Susan Sportsman", "6th", "Elsevier", 2022, "Nursing Leadership", 10, "Leading teams and managing care delivery."),
        ("Ethics and Issues in Contemporary Nursing", "Margaret A. Burkhardt and Alvita K. Nathaniel", "4th", "Cengage", 2019, "Nursing Ethics", 10, "Ethical reasoning in nursing dilemmas."),
        ("Legal and Ethical Issues in Nursing", "Guido W. Guinness", "7th", "Pearson", 2019, "Nursing Ethics", 8, "Law, liability, and advocacy for nurses."),
        ("Nursing Informatics and the Foundation of Knowledge", "Dee McGonigle and Kathleen Mastrian", "5th", "Jones and Bartlett", 2021, "Nursing Informatics", 8, "Data, information, and technology in nursing."),
        ("Emergency Nursing: Principles and Practice", "Gail P. Lenehan", "1st", "Elsevier", 2019, "Emergency Nursing", 8, "Triage and emergency department nursing."),
        ("Critical Care Nursing: A Holistic Approach", "Patricia Gonce Morton and Dorrie K. Fontaine", "12th", "Wolters Kluwer", 2023, "Critical Care Nursing", 10, "Holistic management of critically ill patients."),
        ("Gerontologic Nursing", "Annette G. Lueckenotte and Mary Ann Sherman", "6th", "Elsevier", 2021, "Gerontologic Nursing", 8, "Care of older adults across settings."),
        ("Maternity and Women's Health Care", "Deitra Leonard Lowdermilk, Shannon E. Perry, and Mary Catherine Cashion", "13th", "Elsevier", 2023, "Maternal and Child Nursing", 10, "Evidence-based maternity nursing."),
        ("Wong's Nursing Care of Infants and Children", "Marilyn J. Hockenberry and Cheryl C. Rodgers", "12th", "Elsevier", 2023, "Pediatric Nursing", 10, "Family-centered pediatric nursing."),
        ("Davis's Drug Guide for Nurses", "April Hazard Vallerand and Cynthia A. Sanoski", "18th", "F. A. Davis", 2023, "Pharmacology", 14, "Quick drug reference for nursing practice."),
        ("Nursing Diagnosis Handbook", "Betty J. Ackley, Gail B. Ladwig, and Mary Beth Flynn Makic", "13th", "Elsevier", 2022, "Nursing Process", 12, "Care planning with NANDA diagnoses."),
        ("Clinical Nursing Skills and Techniques", "Anne Griffin Perry, Patricia A. Potter, Wendy Ostendorf, and Nancy Laplante", "11th", "Elsevier", 2023, "Clinical Skills", 14, "Step-by-step nursing procedures."),
        ("Health Promotion Throughout the Life Span", "Carole Lium Edelman and Elizabeth C. Kudzma", "10th", "Elsevier", 2021, "Health Promotion", 8, "Preventive care for every age group."),
        ("Transcultural Nursing: Concepts, Theories, Research, and Practice", "Marilyn R. McFarland and Hiba B. Wehbe-Alamah", "4th", "McGraw-Hill", 2017, "Transcultural Nursing", 6, "Culturally congruent care theory and practice."),
        ("Disaster Nursing and Emergency Preparedness", "Tener Goodwin Veenema", "5th", "Springer Publishing", 2022, "Emergency Nursing", 6, "All-hazards preparedness for nurses."),
        ("Operating Room Nursing", "Nancy Girard", "1st", "Pearson", 2012, "Perioperative Nursing", 5, "Perioperative roles and sterile technique."),
        ("IV Therapy and Blood Transfusion", "Lynn Hadaway", "1st", "Elsevier", 2019, "Clinical Skills", 6, "Infusion practice and transfusion safety."),
        ("Wound Care Essentials", "Sharon Baranoski and Elizabeth A. Ayello", "5th", "Wolters Kluwer", 2019, "Clinical Skills", 5, "Assessment and management of wounds."),
        ("Diabetes Nursing Care", "Belinda Burke", "1st", "Wiley-Blackwell", 2012, "Medical-Surgical Nursing", 4, "Glycemic management and patient education."),
        ("Oncology Nursing", "Margaret Barton-Burke and Gail M. Wilkes", "7th", "Jones and Bartlett", 2022, "Medical-Surgical Nursing", 5, "Cancer care across the trajectory."),
        ("Cardiovascular Nursing", "Susan L. Woods, Erika S. Sivarajan Froelicher, and Sandra Adams Motzer", "8th", "Wolters Kluwer", 2014, "Medical-Surgical Nursing", 5, "Cardiac assessment and interventions."),
        ("Respiratory Nursing", "Alison Pilcher", "1st", "Wiley-Blackwell", 2015, "Medical-Surgical Nursing", 4, "Pulmonary care and ventilation basics."),
        ("Nursing Care Plans: Diagnoses, Interventions, and Outcomes", "Meg Gulanick and Judith L. Myers", "10th", "Elsevier", 2021, "Nursing Process", 10, "Ready-to-use care plans for clinical practice."),
        ("Test Success: Test-Taking Techniques for Beginning Nursing Students", "Patricia M. Nugent and Barbara A. Vitale", "9th", "F. A. Davis", 2021, "Nursing Education", 8, "Strategies for nursing examinations."),
        ("Saunders Comprehensive Review for the NCLEX-RN Examination", "Linda Anne Silvestri and Angela Silvestri", "9th", "Elsevier", 2022, "Nursing Education", 16, "Complete review for licensure examinations."),
        ("Lippincott Q and A Review for NCLEX-RN", "Diane Billings", "13th", "Wolters Kluwer", 2022, "Nursing Education", 12, "Thousands of practice questions with rationales."),
        ("Nursing Theories and Nursing Practice", "Marlaine C. Smith and Marilyn E. Parker", "6th", "F. A. Davis", 2023, "Nursing Theory", 6, "Major nursing theories and their application."),
        ("Philippine Nursing Law and Jurisprudence", "Carmelita C. Divinagracia", "4th", "C and E Publishing", 2018, "Nursing Ethics", 10, "RA 9173 and legal responsibilities of Filipino nurses."),
        ("Community Health Nursing in the Philippines", "Celenia A. Paragas", "2nd", "Educational Publishing House", 2010, "Community Health Nursing", 8, "DOH programs and barangay health practice."),
        ("Holistic Nursing: A Handbook for Practice", "Barbara Montgomery Dossey and Lynn Keegan", "8th", "Jones and Bartlett", 2020, "Holistic Nursing", 1, "Integrative healing modalities in nursing."),
    ],
    # -------------------------------------------------------------------- BPE
    "Bachelor of Physical Education": [
        ("Foundations of Physical Education, Exercise Science, and Sport", "Deborah A. Wuest and Jennifer L. Fisette", "20th", "McGraw-Hill", 2021, "Foundations of PE", 18, "History, philosophy, and careers in physical education."),
        ("Introduction to Physical Education, Fitness, and Sport", "Daryl Siedentop and Hans van der Mars", "9th", "McGraw-Hill", 2019, "Foundations of PE", 14, "Meaning and scope of movement professions."),
        ("Motor Learning and Performance", "Richard A. Schmidt and Timothy D. Lee", "6th", "Human Kinetics", 2019, "Motor Learning", 14, "Principles of skill acquisition and performance."),
        ("Motor Development and Learning in Physical Education", "David L. Gallahue and John C. Ozmun", "12th", "McGraw-Hill", 2019, "Motor Development", 12, "Lifespan motor development applied to teaching."),
        ("Teaching Physical Education for Learning", "Judith Rink", "8th", "McGraw-Hill", 2019, "PE Pedagogy", 16, "Designing effective PE lessons and units."),
        ("Lesson Planning for Middle School Physical Education", "Michael E. Gosset", "1st", "Human Kinetics", 2019, "PE Pedagogy", 10, "Standards-based lesson design for adolescents."),
        ("Biomechanics of Sport and Exercise", "Peter M. McGinnis", "4th", "Human Kinetics", 2020, "Biomechanics", 14, "Mechanical principles of human movement."),
        ("Basic Biomechanics", "Susan J. Hall", "9th", "McGraw-Hill", 2021, "Biomechanics", 12, "Qualitative and quantitative movement analysis."),
        ("Exercise Physiology: Nutrition, Energy, and Human Performance", "William D. McArdle, Frank I. Katch, and Victor L. Katch", "9th", "Wolters Kluwer", 2023, "Exercise Physiology", 16, "Energy systems and training adaptations."),
        ("Physiology of Sport and Exercise", "W. Larry Kenney, Jack H. Wilmore, and David L. Costill", "8th", "Human Kinetics", 2021, "Exercise Physiology", 12, "Acute and chronic responses to exercise."),
        ("Essentials of Strength Training and Conditioning", "G. Gregory Haff and N. Travis Triplett", "5th", "Human Kinetics", 2021, "Strength and Conditioning", 14, "NSCA guide to program design."),
        ("ACSM's Guidelines for Exercise Testing and Prescription", "American College of Sports Medicine", "11th", "Wolters Kluwer", 2021, "Exercise Prescription", 12, "Gold-standard fitness assessment guidelines."),
        ("Fitness for Life", "Charles B. Corbin and Ruth Lindsey", "7th", "Human Kinetics", 2024, "Fitness", 12, "Lifelong physical activity and wellness."),
        ("Measurement and Evaluation in Physical Education and Exercise Science", "Alan C. Lacy and Skip M. Williams", "8th", "Routledge", 2018, "Assessment in PE", 10, "Tests and measurement in movement sciences."),
        ("Adapted Physical Education and Sport", "Joseph P. Winnick and David L. Porretta", "7th", "Human Kinetics", 2021, "Adapted PE", 10, "Inclusive activity for persons with disabilities."),
        ("Sports Psychology: Concepts and Applications", "Richard H. Cox", "8th", "McGraw-Hill", 2021, "Sport Psychology", 10, "Motivation, anxiety, and team dynamics."),
        ("Foundations of Sport and Exercise Psychology", "Robert S. Weinberg and Daniel Gould", "8th", "Human Kinetics", 2023, "Sport Psychology", 10, "Psychological skills for athletes and coaches."),
        ("Nutrition for Sport and Exercise", "Jackie Berning and Suzanne Nelson Steen", "4th", "Jones and Bartlett", 2019, "Sports Nutrition", 8, "Fueling strategies for active people."),
        ("Sports Nutrition: A Handbook for Professionals", "Christine Karpinski and Christine Rosenbloom", "6th", "Academy of Nutrition and Dietetics", 2017, "Sports Nutrition", 6, "Evidence-based fueling for performance."),
        ("Coaching Principles", "Rainer Martens", "4th", "Human Kinetics", 2012, "Coaching", 10, "ASEP foundations of successful coaching."),
        ("Successful Coaching", "Rainer Martens and Robin S. Vealey", "5th", "Human Kinetics", 2024, "Coaching", 8, "Building character and performance in athletes."),
        ("Sports Officiating: A Legal Approach", "Jerry Grunska", "2nd", "Human Kinetics", 2009, "Sports Management", 5, "Rules, ethics, and liability in officiating."),
        ("Basketball: Steps to Success", "Hal Wissel and Kathy Biscontini", "4th", "Human Kinetics", 2021, "Team Sports", 10, "Fundamentals and drills for basketball."),
        ("Volleyball: Steps to Success", "Becky Schmidt", "2nd", "Human Kinetics", 2024, "Team Sports", 8, "Skills progression for volleyball players."),
        ("Football: Steps to Success", "Tom Bass", "2nd", "Human Kinetics", 2012, "Team Sports", 6, "Techniques and tactics for football."),
        ("Swimming: Steps to Success", "Ernest W. Maglischo", "2nd", "Human Kinetics", 2021, "Aquatics", 8, "Stroke mechanics and training sets."),
        ("Track and Field: Steps to Success", "Gus Everett", "1st", "Human Kinetics", 2019, "Athletics", 6, "Events technique and conditioning."),
        ("Badminton: Steps to Success", "Tony Grice", "2nd", "Human Kinetics", 2007, "Racket Sports", 8, "Strokes, footwork, and strategy."),
        ("Tennis: Steps to Success", "Jim Brown and Camilo Villegas", "4th", "Human Kinetics", 2019, "Racket Sports", 6, "Groundstrokes to match play."),
        ("Arnis: History and Techniques of Filipino Martial Arts", "Mark V. Wiley", "1st", "Tuttle Publishing", 2012, "Filipino Martial Arts", 12, "National sport of the Philippines: history and basics."),
        ("Fundamentals of Dance", "Miriam P. Aquino", "2nd", "Rex Book Store", 2015, "Dance", 10, "Philippine folk, social, and creative dance."),
        ("Philippine Folk Dances", "Francisca Reyes-Aquino", "Reprint", "National Book Store", 2008, "Dance", 10, "Classic collection of Filipino folk dances."),
        ("Rhythmic Activities and Dance", "John Price Bennett and Pamela C. Riemer", "2nd", "Human Kinetics", 2006, "Dance", 6, "Teaching rhythm and movement fundamentals."),
        ("First Aid, CPR, and AED", "American Red Cross", "8th", "Jones and Bartlett", 2021, "First Aid", 12, "Emergency response knowledge and skills."),
        ("Care and Prevention of Athletic Injuries", "William E. Prentice", "10th", "McGraw-Hill", 2013, "Sports Medicine", 8, "Recognition and rehabilitation of injuries."),
        ("Sports Medicine Essentials", "Jim Clover and Mike Wall", "3rd", "Cengage", 2015, "Sports Medicine", 6, "Core concepts for the sports medicine team."),
        ("Kinesiology: Scientific Basis of Human Motion", "Marilyn Hamilton, Luttgens Kinesiology", "12th", "McGraw-Hill", 2011, "Kinesiology", 8, "Anatomical analysis of movement."),
        ("Dance Teaching Methods and Curriculum Design", "Gayle Kassing and Danielle M. Jay", "2nd", "Human Kinetics", 2020, "Dance", 5, "Comprehensive dance education methods."),
        ("Health Education: Elementary and Middle School Applications", "Susan K. Telljohann, Cynthia E. Symons, and Beth Pateman", "9th", "McGraw-Hill", 2019, "Health Education", 8, "School health instruction strategies."),
        ("Outdoor Recreation and Camping", "Department of Education Philippines", "1st", "DepEd", 2016, "Outdoor Education", 6, "Camping, hiking, and outdoor leadership basics."),
        ("Recreational Leadership", "Miriam G. Reboredo", "1st", "Rex Book Store", 2014, "Recreation", 5, "Planning community recreation programs."),
        ("Sports Management: Principles and Applications", "Russell Hoye, Aaron C. T. Smith, and Matthew Nicholson", "6th", "Routledge", 2021, "Sports Management", 5, "Governance and management of sport organizations."),
        ("Yoga Anatomy", "Leslie Kaminoff and Amy Matthews", "3rd", "Human Kinetics", 2021, "Fitness", 4, "Muscles and alignment in yoga postures."),
        ("Weight Training: Steps to Success", "Thomas R. Baechle and Roger W. Earle", "5th", "Human Kinetics", 2019, "Strength and Conditioning", 1, "Progressive resistance training programs."),
    ],
    # -------------------------------------------------------------------- BPA
    "Bachelor of Public Administration": [
        ("Understanding Public Administration", "Seung C. Lee and David H. Rosenbloom", "1st", "Routledge", 2024, "Public Administration Theory", 18, "Contemporary introduction to the field."),
        ("Public Administration: Concepts and Cases", "Richard J. Stillman II", "9th", "Cengage", 2009, "Public Administration Theory", 14, "Classic cases illustrating administrative theory."),
        ("Classics of Public Administration", "Jay M. Shafritz and Albert C. Hyde", "8th", "Cengage", 2016, "Public Administration Theory", 12, "Foundational readings from Wilson to Waldo."),
        ("Introducing Public Administration", "Jay M. Shafritz, E. W. Russell, Christopher P. Borick, and Albert C. Hyde", "10th", "Routledge", 2022, "Public Administration Theory", 14, "Core functions and issues of public management."),
        ("Public Administration in the Philippines", "Victoria A. Bautista", "2nd", "University of the Philippines Press", 2014, "Philippine Public Administration", 16, "History and practice of Philippine bureaucracy."),
        ("Bureaucracy and Governance in the Philippines", "Danilo R. Reyes", "1st", "University of the Philippines Press", 2008, "Philippine Public Administration", 10, "Reform and politics of the civil service."),
        ("Local Government in the Philippines", "Jose N. Endriga", "1st", "University of the Philippines Press", 2001, "Local Governance", 14, "Decentralization under the Local Government Code."),
        ("The Local Government Code of 1991: Annotations", "Aquilino Q. Pimentel Jr.", "2nd", "Rex Book Store", 2013, "Local Governance", 12, "Annotated RA 7160 for local officials."),
        ("Public Policy: Politics, Analysis, and Alternatives", "Michael E. Kraft and Scott R. Furlong", "8th", "CQ Press", 2023, "Public Policy", 14, "Stages and analysis of policymaking."),
        ("The Policy Process: A Reader", "Michael S. Hill and Frederic Varone", "3rd", "Routledge", 2021, "Public Policy", 8, "Key readings on agenda-setting to evaluation."),
        ("Policy Analysis: Concepts and Practice", "David L. Weimer and Aidan R. Vining", "6th", "Routledge", 2017, "Policy Analysis", 8, "Methods for analyzing policy alternatives."),
        ("Public Budgeting Systems", "Robert D. Lee Jr., Ronald W. Johnson, and Philip G. Joyce", "10th", "Jones and Bartlett", 2020, "Public Finance", 14, "Budget processes and fiscal administration."),
        ("Government Budgeting and Expenditure Management", "Salvatore Schiavo-Campo", "1st", "Routledge", 2017, "Public Finance", 8, "Budget reform and expenditure control."),
        ("Philippine Public Fiscal Administration", "Danilo R. Reyes and Ledivina V. Carino", "1st", "University of the Philippines Press", 2000, "Public Finance", 8, "Taxation, budgeting, and audit in the Philippines."),
        ("Human Resource Management in Public Service", "Evan M. Berman, James S. Bowman, Jonathan P. West, and Montgomery R. Van Wart", "6th", "SAGE Publications", 2020, "Human Resource Management", 12, "Paradoxes and practices of public HRM."),
        ("Public Personnel Management", "Norma M. Riccucci", "6th", "Routledge", 2021, "Human Resource Management", 8, "Merit systems and civil service reform."),
        ("Organization Theory and the Public Sector", "Tom Christensen, Per Laegreid, and Kjell Arne Rovik", "2nd", "Routledge", 2020, "Organization Theory", 10, "Instrumental, cultural, and myth perspectives."),
        ("Understanding and Managing Public Organizations", "Hal G. Rainey, Sergio Fernandez, and Deanna Malatesta", "6th", "Jossey-Bass", 2021, "Organization Theory", 10, "Behavior and management of public agencies."),
        ("Leadership in Public Organizations", "Montgomery R. Van Wart", "4th", "Routledge", 2022, "Public Leadership", 8, "Competencies for administrative leadership."),
        ("Administrative Law", "Owen M. Fiss", "1st", "Foundation Press", 2018, "Administrative Law", 10, "Judicial control of administrative action."),
        ("Philippine Administrative Law", "Melchor G. Villanueva", "3rd", "Rex Book Store", 2016, "Administrative Law", 10, "Powers and procedures of Philippine agencies."),
        ("Ethics in Public Management", "H. George Frederickson and Richard K. Ghere", "2nd", "Routledge", 2013, "Public Ethics", 8, "Administrative ethics and accountability."),
        ("Public Service Ethics", "James S. Bowman and Jonathan P. West", "2nd", "Routledge", 2021, "Public Ethics", 6, "Individual and organizational integrity."),
        ("Performance Management and Evaluation", "Jack E. Edwards and Scott L. Lacefield", "1st", "SAGE Publications", 2019, "Public Management", 6, "Measuring results in government programs."),
        (" Managing Public Sector Projects", "Graham M. Winch", "1st", "Cambridge University Press", 2022, "Project Management", 5, "Delivering public infrastructure and programs."),
        ("E-Government in the Philippines", "Emmanuel C. Lallana", "1st", "National Computer Center", 2015, "E-Governance", 6, "Digital government initiatives and lessons."),
        ("Digital Government: Technology and Public Sector Performance", "Darrell M. West", "1st", "Brookings Institution Press", 2005, "E-Governance", 5, "How technology reshapes government services."),
        ("Public-Private Partnerships", "E. R. Yescombe and Edward Farquharson", "2nd", "Elsevier", 2018, "Public Management", 5, "Structuring PPP deals and contracts."),
        ("Disaster Risk Reduction and Management in the Philippines", "Office of Civil Defense", "1st", "NDRRMC", 2017, "Disaster Management", 8, "RA 10121 framework and local DRRM practice."),
        ("Introduction to Emergency Management", "George Haddow, Jane Bullock, and Damon Coppola", "7th", "Elsevier", 2020, "Disaster Management", 6, "Phases of emergency management."),
        ("Urban Planning and Governance", "Pablo V. Acuna", "1st", "University of the Philippines Press", 2012, "Urban Planning", 6, "Land use and city management in the Philippines."),
        ("The City Reader", "Richard T. LeGates and Frederic Stout", "7th", "Routledge", 2020, "Urban Planning", 4, "Essential urban studies anthology."),
        ("Development Administration", "Ledivina V. Carino", "1st", "University of the Philippines Press", 1992, "Development Administration", 8, "Classic Filipino text on development management."),
        ("New Public Management", "Christopher Hood", "1st", "Oxford University Press", 2010, "Public Management", 4, "Market reforms and managerialism debates."),
        ("Governance and Politics of the Philippines", "Teresa S. Encarnacion Tadem and Noel M. Morada", "1st", "Oxford University Press", 2006, "Philippine Politics", 8, "State, regime, and governance analysis."),
        ("Philippine Politics and Governance", "Alex B. Brillantes Jr. and Maricel T. Fernandez", "2nd", "University of the Philippines Press", 2011, "Philippine Politics", 10, "Institutions and processes of Filipino governance."),
        ("Civil Society in the Philippines", "Gerard Clarke", "1st", "Routledge", 2013, "Civil Society", 5, "NGOs and people power in development."),
        ("Nonprofit Management", "Michael J. Worth", "7th", "SAGE Publications", 2023, "Nonprofit Management", 5, "Principles for mission-driven organizations."),
        ("Research Methods for Public Administrators", "Gary Rassel, Suzanne Leland, Zachary Mohr, and Elizabeth O'Sullivan", "7th", "Routledge", 2020, "Research Methods", 8, "Quantitative and qualitative methods for MPA students."),
        ("Statistics for Public Administration", "Evan M. Berman and Xiaohu Wang", "5th", "SAGE Publications", 2021, "Statistics", 6, "Applied statistics for administrators."),
        ("Public Procurement: Rules and Practice", "Government Procurement Policy Board", "1st", "GPPB", 2019, "Procurement", 8, "RA 12009 procurement rules and procedures."),
        ("Administrative Reforms in Asia", "Jon S. T. Quah", "1st", "Emerald", 2016, "Comparative Administration", 4, "Anti-corruption and reform across Asia."),
        ("Comparative Public Administration", "Eric E. Otenyo and Nancy S. Lind", "1st", "Emerald", 2006, "Comparative Administration", 4, "Administrative systems across countries."),
        ("Theories of Governance", "R. A. W. Rhodes", "1st", "Routledge", 2018, "Governance", 1, "Networks, hollowing out, and meta-governance."),
    ],
    # ------------------------------------------------------------------ CRIM
    "BS Criminology": [
        ("Criminology: Theories, Patterns, and Typologies", "Larry J. Siegel", "14th", "Cengage", 2023, "Criminology", 20, "Major theories of crime causation and typologies."),
        ("Criminology Today: An Integrative Introduction", "Frank Schmalleger", "10th", "Pearson", 2023, "Criminology", 16, "Contemporary overview of crime and justice."),
        ("Introduction to Criminal Justice", "Larry J. Siegel and John L. Worrall", "17th", "Cengage", 2023, "Criminal Justice", 18, "Police, courts, and corrections systems."),
        ("Criminal Justice in the Philippines", "Ricardo M. Guevara", "3rd", "Rex Book Store", 2018, "Philippine Criminal Justice", 16, "Five pillars of the Philippine justice system."),
        ("The Revised Penal Code of the Philippines: Annotated", "Luis B. Reyes", "20th", "Rex Book Store", 2021, "Criminal Law", 20, "Standard annotation of Act No. 3815."),
        ("Criminal Law: Fundamentals", "Dean Antonio S. Bautista", "1st", "Rex Book Store", 2017, "Criminal Law", 12, "Felonies, penalties, and criminal liability."),
        ("Fundamentals of Criminal Investigation", "Charles E. O'Hara and Gregory L. O'Hara", "9th", "Charles C. Thomas", 2014, "Criminal Investigation", 16, "Techniques of crime detection and case building."),
        ("Criminal Investigation", "Michael D. Lyman", "12th", "Pearson", 2023, "Criminal Investigation", 14, "Modern investigative methods and forensics."),
        ("Practical Criminal Investigation", "Manuel L. Quebral", "2nd", "Wisdom Advocate", 2015, "Criminal Investigation", 10, "Philippine-focused investigative procedures."),
        ("Criminalistics: An Introduction to Forensic Science", "Richard Saferstein", "13th", "Pearson", 2023, "Forensic Science", 16, "Crime lab methods from DNA to fingerprints."),
        ("Forensic Science: From the Crime Scene to the Crime Lab", "Richard Saferstein", "4th", "Pearson", 2019, "Forensic Science", 12, "Field-to-lab forensic workflow."),
        ("Death Investigation and Examination", "R. T. B. Cruz", "1st", "Rex Book Store", 2016, "Forensic Science", 8, "Medico-legal investigation in the Philippines."),
        ("Fingerprint Identification", "Ramon C. Sarmiento", "2nd", "Rex Book Store", 2014, "Dactyloscopy", 10, "Classification and comparison of fingerprints."),
        ("Questioned Documents Examination", "Brenda M. Nicolas", "1st", "Wisdom Advocate", 2013, "Questioned Documents", 8, "Handwriting and document fraud analysis."),
        ("Forensic Ballistics", "Felipe B. Ramos", "2nd", "Rex Book Store", 2015, "Forensic Ballistics", 10, "Firearms, cartridges, and bullet comparison."),
        ("Polygraphy: The Science of Lie Detection", "Leonardo A. de Castro", "1st", "Wisdom Advocate", 2012, "Polygraphy", 6, "Theory and practice of polygraph examination."),
        ("Police Patrol Operations", "Dionisio R. Flores", "3rd", "Rex Book Store", 2017, "Law Enforcement", 12, "Patrol methods and police operations."),
        ("Police Administration and Management", "Cordell W. Huey", "1st", "Rex Book Store", 2016, "Law Enforcement", 10, "Organizing and leading police agencies."),
        ("Community Policing: A Contemporary Perspective", "Victor E. Kappeler and Larry K. Gaines", "8th", "Routledge", 2020, "Law Enforcement", 8, "Partnership and problem-solving policing."),
        ("Traffic Management and Accident Investigation", "Carlito D. Marquez", "2nd", "Rex Book Store", 2015, "Traffic Management", 10, "Enforcement and crash investigation."),
        ("Introduction to Corrections", "Robert D. Hanser", "3rd", "SAGE Publications", 2019, "Corrections", 12, "Institutions, probation, and rehabilitation."),
        ("Philippine Correctional System", "Ferdinand M. Santos", "1st", "Rex Book Store", 2016, "Corrections", 10, "BuCor, BJMP, and parole-probation administration."),
        ("Probation and Parole", "Howard Abadinsky", "12th", "Pearson", 2017, "Corrections", 8, "Community supervision theory and practice."),
        ("Court Testimony and Evidence", "Miguel C. Contreras", "1st", "Central Book Supply", 2014, "Evidence", 8, "Rules of evidence and witness examination."),
        ("Rules of Court of the Philippines: Criminal Procedure", "Supreme Court of the Philippines", "A.M. Updates", "Rex Book Store", 2023, "Criminal Procedure", 12, "Criminal procedure rules and jurisprudence."),
        ("Human Rights and Law Enforcement", "Commission on Human Rights Philippines", "1st", "CHR", 2016, "Human Rights", 8, "Rights-based policing standards."),
        ("Vice Control and Drug Enforcement", "Dangerous Drugs Board", "1st", "DDB", 2018, "Drug Enforcement", 10, "RA 9165 and anti-drug operations."),
        ("Drugs and Society", "Glen R. Hanson, Peter J. Venturelli, and Annette E. Fleckenstein", "14th", "Jones and Bartlett", 2020, "Drug Education", 8, "Pharmacology and policy of abused drugs."),
        ("Criminological Theory", "Frank P. Williams III and Marilyn D. McShane", "7th", "Pearson", 2020, "Criminology", 8, "Classical to contemporary theory."),
        ("Victimology: The Study of the Victim", "Judy H. Eaton", "1st", "Routledge", 2021, "Victimology", 6, "Victims' roles, rights, and services."),
        ("Juvenile Delinquency", "Clemens Bartollas and Stuart J. Miller", "10th", "Pearson", 2019, "Juvenile Delinquency", 8, "Causes and control of youth crime."),
        ("Juvenile Justice in the Philippines", "Corazon Alma G. de Leon", "1st", "Rex Book Store", 2013, "Juvenile Delinquency", 8, "RA 9344 and child-in-conflict-with-law practice."),
        ("Terrorism and Homeland Security", "Jonathan R. White", "10th", "Cengage", 2023, "Terrorism", 6, "Counterterrorism strategy and policy."),
        ("Private Security Management", "Charles P. Nemeth", "2nd", "CRC Press", 2022, "Security Management", 6, "Guard forces and corporate security."),
        ("Industrial Security Management", "Emmanuel Q. Villar", "1st", "Rex Book Store", 2015, "Security Management", 6, "Facility and plant protection."),
        ("Cybercrime Investigation", "John Bandler and Antonia Merzon", "2nd", "Routledge", 2023, "Cybercrime", 8, "Digital evidence and cyber offenses."),
        ("Computer Forensics", "Marie-Helen Maras", "2nd", "Jones and Bartlett", 2014, "Cybercrime", 5, "Acquisition and analysis of digital evidence."),
        ("Arson Investigation", "Enrique T. Baking", "1st", "Wisdom Advocate", 2014, "Arson Investigation", 6, "Fire cause and origin determination."),
        ("First Aid for Law Enforcers", "Philippine National Police", "1st", "PNP Directorate", 2017, "First Aid", 6, "Tactical casualty care basics."),
        ("Criminal Sociology", "Isabelo R. Cristobal", "1st", "Rex Book Store", 2012, "Criminology", 6, "Social roots of criminal behavior."),
        ("Research Methods in Criminal Justice and Criminology", "Frank E. Hagan and Leah E. Daigle", "12th", "Pearson", 2023, "Research Methods", 8, "Designs and statistics for justice research."),
        ("Statistics for Criminology", "Avelino P. Sebastian", "1st", "Rex Book Store", 2016, "Statistics", 6, "Descriptive statistics for criminology students."),
        ("Intelligence and National Security", "Wilfredo O. Garcia", "1st", "Rex Book Store", 2015, "Intelligence", 5, "Intelligence cycle and state security."),
        ("Gun Safety and Marksmanship", "NROI Philippines", "1st", "NROI", 2019, "Marksmanship", 4, "Safe handling and fundamentals of shooting."),
        ("Criminology Board Examination Reviewer", "Ramon S. Garcia", "6th", "Rex Book Store", 2022, "Board Review", 16, "Comprehensive licensure review questions."),
        ("Forensic Medicine in the Philippines", "Raquel B. del Rosario", "1st", "Central Book Supply", 2011, "Forensic Science", 1, "Medico-legal practice and autopsy procedure."),
    ],
    # -------------------------------------------------------------------- ECE
    "Early Childhood Education": [
        ("Developmentally Appropriate Practice in Early Childhood Programs", "Sue Bredekamp and Carol Copple", "4th", "NAEYC", 2021, "Early Childhood Education", 18, "NAEYC position statement on quality practice."),
        ("The Creative Curriculum for Preschool", "Diane Trister Dodge, Laura J. Colker, and Cate Heroman", "6th", "Teaching Strategies", 2016, "Early Childhood Curriculum", 16, "Project-based preschool curriculum framework."),
        ("Child Development", "Laura E. Berk", "7th", "Pearson", 2021, "Child Development", 18, "Physical, cognitive, and social development."),
        ("Child Development: A Topical Approach", "Robert S. Feldman", "1st", "Pearson", 2018, "Child Development", 12, "Topical survey from infancy to adolescence."),
        ("Infants, Toddlers, and Caregivers", "Janet Gonzalez-Mena and Dianne Widmeyer Eyer", "11th", "McGraw-Hill", 2020, "Infant and Toddler Care", 12, "Relationship-based caregiving routines."),
        ("Guiding Children's Social Development and Learning", "Marjorie V. Fields, Patricia A. Meritt, and Deborah M. Fields", "9th", "Cengage", 2017, "Child Guidance", 12, "Positive guidance and classroom community."),
        ("Positive Discipline in the Classroom", "Jane Nelsen, Lynn Lott, and H. Stephen Glenn", "4th", "Harmony", 2013, "Child Guidance", 8, "Class meetings and mutual respect tools."),
        ("Early Childhood Literacy", "Timothy Shanahan and Christopher J. Lonigan", "1st", "Brookes Publishing", 2012, "Early Literacy", 12, "Research on preschool reading development."),
        ("Beginning to Read: Thinking and Learning about Print", "Marilyn Jager Adams", "Reprint", "MIT Press", 1994, "Early Literacy", 8, "Landmark synthesis on learning to read."),
        ("Teaching Mathematics in the Primary Grades", "Angelica C. Mendoza", "1st", "Rex Book Store", 2017, "Early Mathematics", 10, "Concrete-pictorial-abstract math instruction."),
        ("Mathematics Learning in Early Childhood", "National Research Council", "1st", "National Academies Press", 2009, "Early Mathematics", 6, "Paths toward excellence in early math."),
        ("Health, Safety, and Nutrition for the Young Child", "Lynn R. Marotz", "10th", "Cengage", 2019, "Child Health and Nutrition", 10, "Wellness practices in early childhood settings."),
        ("Observing and Recording the Behavior of Young Children", "Dorothy H. Cohen, Virginia Stern, and Nancy Balaban", "6th", "Teachers College Press", 2016, "Child Observation", 8, "Anecdotal records and running records."),
        ("Assessing and Guiding Young Children's Development and Learning", "Oralie McAfee, Deborah J. Leong, and Elena Bodrova", "6th", "Pearson", 2015, "Assessment", 8, "Authentic assessment in preschool."),
        ("Play: How It Shapes the Brain", "David Elkind", "1st", "Broadway Books", 2007, "Play", 8, "The power of play in development."),
        ("The Importance of Play in Early Childhood Education", "Kristine M. Slentz", "1st", "Routledge", 2016, "Play", 6, "Play-based learning theory and advocacy."),
        ("Music and Movement for Young Children", "Linda Carol Edwards, Kathleen M. Bayless, and Marjorie E. Ramsey", "8th", "Cengage", 2017, "Music and Movement", 8, "Songs, rhythm, and creative movement."),
        ("Art and Creative Development for Young Children", "Robert Schirrmacher and Joan E. Fox", "9th", "Cengage", 2020, "Creative Arts", 8, "Process art across early childhood."),
        ("Science in Early Childhood", "Rebecca L. Garibay", "1st", "Rex Book Store", 2018, "Early Science", 6, "Inquiry activities for young scientists."),
        ("Language Development in Early Childhood", "Beverly Otto", "5th", "Pearson", 2017, "Language Development", 10, "Stages and support of oral language."),
        ("Mother Tongue-Based Multilingual Education", "Department of Education Philippines", "1st", "DepEd", 2016, "Language Development", 8, "MTB-MLE policy and classroom practice."),
        ("Including Children with Special Needs", "Marites P. Querol", "1st", "Rex Book Store", 2019, "Inclusive Education", 8, "Mainstreaming in Philippine preschools."),
        ("Anti-Bias Education for Young Children and Ourselves", "Louise Derman-Sparks and Julie Olsen Edwards", "2nd", "NAEYC", 2020, "Diversity", 6, "Equity goals for early childhood programs."),
        ("Families, Schools, and Communities", "Donna Couchenour and Kent Chrisman", "6th", "Cengage", 2016, "Family Partnerships", 8, "Building home-school collaboration."),
        ("Parent-Teacher Partnerships", "Lorna M. Espinosa", "1st", "Rex Book Store", 2017, "Family Partnerships", 6, "Engaging Filipino families in schooling."),
        ("Classroom Management for Elementary Teachers", "Carolyn M. Evertson and Edmund T. Emmer", "11th", "Pearson", 2020, "Classroom Management", 8, "Organizing productive elementary classrooms."),
        ("Kindergarten Curriculum Guide", "Department of Education Philippines", "Revised", "DepEd", 2019, "Curriculum", 10, "Official Philippine kindergarten standards."),
        ("Early Childhood Education in the Philippines", "Fe A. Hidalgo", "1st", "Rex Book Store", 2015, "Early Childhood Education", 10, "RA 8980 and the ECCD system."),
        ("Child Psychology and Development", "Evelyn M. Fernando", "2nd", "Rex Book Store", 2018, "Child Development", 8, "Filipino-context developmental psychology."),
        ("Storytelling with Children", "Nancy Mellon", "1st", "Hawthorn Press", 2013, "Early Literacy", 5, "Oral storytelling techniques for teachers."),
        ("Big Books for Little Readers", "Corazon S. Morilla", "1st", "Adarna House", 2016, "Early Literacy", 6, "Using big books in Filipino classrooms."),
        ("Filipino Children's Literature", "Virgilio S. Almario", "1st", "Adarna House", 2014, "Children's Literature", 6, "Anthology and criticism of local stories."),
        ("Children's Literature in the Elementary School", "Charlotte S. Huck and Barbara Kiefer", "11th", "McGraw-Hill", 2019, "Children's Literature", 6, "Genres and selection of children's books."),
        ("Teaching Beginning Reading", "Rosita L. Navarro", "1st", "Rex Book Store", 2017, "Early Literacy", 8, "Phonics and whole-language balance."),
        ("Games for Early Learning", "Priscilla M. Santos", "1st", "Rex Book Store", 2016, "Play", 5, "Low-cost learning games for preschools."),
        ("Nutrition for Young Children", "Food and Nutrition Research Institute", "1st", "DOST-FNRI", 2018, "Child Health and Nutrition", 5, "Pinggang Pinoy and feeding guidelines."),
        ("Child Protection Policy Guide", "Department of Education Philippines", "1st", "DepEd", 2012, "Child Protection", 6, "DepEd Order 40 on child protection."),
        ("Educating Young Children with Autism", "Clara L. Cruz", "1st", "Rex Book Store", 2020, "Inclusive Education", 4, "Classroom supports for learners with autism."),
        ("The Whole-Brain Child", "Daniel J. Siegel and Tina Payne Bryson", "1st", "Bantam", 2012, "Child Development", 1, "Brain-based strategies for caregivers."),
    ],
    # ------------------------------------------------------------------- SNED
    "Special Needs Education": [
        ("Exceptional Children: An Introduction to Special Education", "William L. Heward, Sheila R. Alber-Morgan, and Moira Konrad", "12th", "Pearson", 2022, "Special Education", 18, "Characteristics and teaching of exceptional learners."),
        ("Special Education: Contemporary Perspectives for School Professionals", "Marilyn Friend", "6th", "Pearson", 2023, "Special Education", 16, "Collaboration and inclusive practices."),
        ("Teaching Students with Special Needs in Inclusive Settings", "Tom E. C. Smith, Edward A. Polloway, James R. Patton, and Carol A. Dowdy", "7th", "Pearson", 2019, "Inclusive Education", 16, "Adapting instruction for diverse classrooms."),
        ("Inclusive Education in the Philippines", "Yolanda S. Quijano", "1st", "Rex Book Store", 2016, "Inclusive Education", 14, "RA 11650 and Philippine inclusive practice."),
        ("Educating Children with Autism", "National Research Council", "1st", "National Academies Press", 2001, "Autism", 12, "Evidence on early autism intervention."),
        ("A Parent's Guide to High-Functioning Autism", "Sally Ozonoff, Geraldine Dawson, and James C. McPartland", "2nd", "Guilford Press", 2014, "Autism", 8, "Practical strategies for families and teachers."),
        ("Teaching Children with Autism", "Marjorie H. Charlop, Russell Lang, and Mandy Rispoli", "1st", "Springer", 2018, "Autism", 8, "Behavioral interventions in classrooms."),
        ("Learning Disabilities: Foundations, Characteristics, and Effective Teaching", "Daniel P. Hallahan, James M. Kauffman, and Paige C. Pullen", "5th", "Pearson", 2022, "Learning Disabilities", 12, "Identification and instruction for LD."),
        ("Teaching Students with Learning Disabilities", "Lorna O. Hernandez", "1st", "Rex Book Store", 2018, "Learning Disabilities", 8, "Local strategies for struggling learners."),
        ("ADHD: What Every Parent Needs to Know", "Mark L. Wolraich and George J. DuPaul", "3rd", "American Academy of Pediatrics", 2019, "ADHD", 8, "Diagnosis and school supports for ADHD."),
        ("Teaching Young Children with ADHD", "George J. DuPaul and Lee Kern", "1st", "Guilford Press", 2011, "ADHD", 6, "Classroom interventions that work."),
        ("Intellectual Disability: Definition, Classification, and Systems of Supports", "American Association on Intellectual and Developmental Disabilities", "12th", "AAIDD", 2021, "Intellectual Disability", 10, "Supports-based paradigm for ID."),
        ("Down Syndrome: Care and Education", "Teresita C. Castillo", "1st", "Rex Book Store", 2017, "Intellectual Disability", 6, "Developmental and school guidance."),
        ("Hearing Impairment and Deaf Education", "Marc Marschark and Patricia E. Spencer", "2nd", "Oxford University Press", 2015, "Deaf Education", 8, "Language and literacy for deaf learners."),
        ("Teaching Deaf Learners", "Harry Knoors and Maria Marschark", "1st", "Oxford University Press", 2014, "Deaf Education", 6, "Psychological and educational foundations."),
        ("Visual Impairment: Education and Rehabilitation", "Corazon B. Salazar", "1st", "Rex Book Store", 2016, "Visual Impairment", 6, "Braille, mobility, and classroom access."),
        ("Physical Disabilities and Health Impairments", "Elena P. Garcia", "1st", "Rex Book Store", 2018, "Physical Disabilities", 6, "School accommodation and assistive care."),
        ("Gifted and Talented Learners", "Sally M. Reis and Joseph S. Renzulli", "1st", "Routledge", 2018, "Gifted Education", 8, "Enrichment and acceleration models."),
        ("Teaching Gifted Children in Today's Classrooms", "Susan Winebrenner and Dina Brulles", "Revised", "Free Spirit", 2018, "Gifted Education", 6, "Differentiation strategies that challenge."),
        ("Behavior Management: Principles and Practices", "John J. Wheeler and David D. Richey", "3rd", "Pearson", 2019, "Behavior Management", 10, "Positive behavior supports in schools."),
        ("Functional Behavioral Assessment and Intervention", "Robert E. O'Neill, Richard W. Albin, Keith Storey, and Robert H. Horner", "2nd", "Cengage", 2014, "Behavior Management", 6, "FBA process and behavior plans."),
        ("Assistive Technology for Students with Disabilities", "Diana L. Bryant and Brian R. Bryant", "5th", "Pearson", 2019, "Assistive Technology", 8, "Devices and software enabling access."),
        ("Augmentative and Alternative Communication", "David R. Beukelman and Janice C. Light", "5th", "Brookes Publishing", 2020, "Assistive Technology", 5, "AAC systems across the lifespan."),
        ("Speech and Language Disorders in Children", "Rhea Paul, Courtenay F. Norbury, and Carolyn Gosse", "6th", "Elsevier", 2024, "Speech and Language", 8, "Assessment and intervention for communication disorders."),
        ("Early Intervention for Young Children", "Rosario M. Alonzo", "1st", "Rex Book Store", 2019, "Early Intervention", 8, "Family-centered early intervention practice."),
        ("Individualized Education Programs", "Department of Education Philippines", "1st", "DepEd", 2020, "IEP", 10, "DepEd guidelines on IEP development."),
        ("Assessment in Special Education", "Loraine J. Spenciner and Laura A. Cohen", "1st", "Pearson", 2018, "Assessment", 8, "Formal and informal assessment tools."),
        ("Transition Planning for Students with Disabilities", "Luz T. Fernandez", "1st", "Rex Book Store", 2021, "Transition", 5, "School-to-work transition supports."),
        ("Counseling Families of Children with Special Needs", "Rosa L. Mercado", "1st", "Rex Book Store", 2018, "Family Support", 5, "Partnering with Filipino families."),
        ("Sign Language for Filipino Teachers", "Philippine Federation of the Deaf", "2nd", "PFD", 2019, "Deaf Education", 6, "Filipino Sign Language basics for classrooms."),
        ("Braille Literacy Manual", "Resources for the Blind Philippines", "1st", "RBI", 2017, "Visual Impairment", 4, "Reading and writing braille."),
        ("Occupational Therapy for Children", "Jane Case-Smith and Jane Clifford O'Brien", "8th", "Elsevier", 2019, "Therapy", 6, "OT frames of reference in pediatrics."),
        ("Physical Therapy for Children with Disabilities", "Anita C. Benson", "1st", "Rex Book Store", 2020, "Therapy", 4, "Movement therapy in school settings."),
        ("Emotional and Behavioral Disorders", "Paul Zionts, Laura Zionts, and Richard L. Simpson", "5th", "Corwin", 2016, "Behavior Management", 5, "Theory and intervention for EBD."),
        ("Dyslexia: A Practitioner's Handbook", "Gavin Reid", "5th", "Wiley", 2016, "Learning Disabilities", 5, "Identification and teaching for dyslexia."),
        ("The Out-of-Sync Child", "Carol Stock Kranowitz", "Revised", "TarcherPerigee", 2022, "Sensory Processing", 4, "Sensory processing disorder at home and school."),
        ("Universal Design for Learning", "Anne Meyer, David H. Rose, and David Gordon", "1st", "CAST", 2014, "Inclusive Education", 6, "UDL framework for flexible curricula."),
        ("Differentiated Instruction", "Carol Ann Tomlinson", "3rd", "ASCD", 2017, "Inclusive Education", 1, "Responding to learner variance daily."),
    ],
}

# Program label used inside descriptions (book_catalog has no program FK).
PROGRAM_LABEL = {
    "Bachelor of Arts in Communication": "Bachelor of Arts in Communication",
    "BS Information Systems": "BS Information Systems",
    "BS Mathematics": "BS Mathematics",
    "BS Nursing": "BS Nursing",
    "Bachelor of Physical Education": "Bachelor of Physical Education",
    "Bachelor of Public Administration": "Bachelor of Public Administration",
    "BS Criminology": "BS Criminology",
    "Early Childhood Education": "Early Childhood Education",
    "Special Needs Education": "Special Needs Education",
}

CALL_PREFIX = {
    "Bachelor of Arts in Communication": "P90",
    "BS Information Systems": "QA76",
    "BS Mathematics": "QA",
    "BS Nursing": "RT",
    "Bachelor of Physical Education": "GV",
    "Bachelor of Public Administration": "JF",
    "BS Criminology": "HV",
    "Early Childhood Education": "LB1140",
    "Special Needs Education": "LC3950",
}


def flatten_books():
    """Yield (program, title, author, edition, publisher, year, subject,
    copies, blurb) in a stable order."""
    for program in PROGRAMS:
        for entry in BOOKS.get(program, []):
            yield (program,) + entry


def isbn13_for(index):
    """Deterministic, unique, check-digit-valid ISBN-13 per title index."""
    core = "%09d" % (100000000 + index * 7919)
    digits = "978" + core  # 12 digits
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    check = (10 - (total % 10)) % 10
    full = digits + str(check)
    return "978-%s-%s-%s-%s" % (full[3], full[4:7], full[7:12], full[12])


def call_number_for(program, index, year):
    prefix = CALL_PREFIX[program]
    cutter = chr(65 + (index % 26)) + str(100 + (index * 37) % 800)
    return "%s.%s %d" % (prefix, cutter, year)


def get_conn(dsn):
    from dotenv import load_dotenv

    load_dotenv()
    dsn = dsn or os.getenv("DATABASE_URL")
    if not dsn:
        sys.exit("No connection string: pass --dsn or set DATABASE_URL in .env")
    # Render-style URLs (postgres://) are rejected by psycopg2.
    if dsn.startswith("postgres://"):
        dsn = "postgresql://" + dsn[len("postgres://"):]
    import psycopg2

    try:
        conn = psycopg2.connect(dsn)
    except Exception as exc:
        sys.exit("Could not connect to Postgres: %s" % exc)
    conn.autocommit = False
    return conn


def ensure_schema(conn):
    """Apply app/schema.sql statement-by-statement (same approach as
    app/database.py:run_schema) so the seeder works on an empty database."""
    schema_path = os.path.join(os.path.dirname(__file__), "app", "schema.sql")
    if not os.path.isfile(schema_path):
        return
    cur = conn.cursor()
    cur.execute(
        "SELECT to_regclass('public.book_catalog'), "
        "to_regclass('public.accession_log'), "
        "to_regclass('public.departments')"
    )
    if all(cur.fetchone()):
        cur.close()
        return
    with open(schema_path, "r", encoding="utf-8") as fh:
        sql = "\n".join(
            line for line in fh.read().splitlines()
            if not line.strip().startswith("--")
        )
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        try:
            cur.execute(stmt)
            conn.commit()
        except Exception:
            conn.rollback()
    cur.close()


def ensure_seed_librarian(cur):
    cur.execute(
        "SELECT user_id FROM user_accounts "
        "WHERE role_id IN (SELECT role_id FROM roles "
        "WHERE role_name IN ('Librarian', 'Admin')) "
        "ORDER BY user_id LIMIT 1"
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("SELECT role_id FROM roles WHERE role_name = 'Librarian'")
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO roles (role_name) VALUES ('Librarian') RETURNING role_id"
        )
        role_id = cur.fetchone()[0]
    else:
        role_id = row[0]
    cur.execute(
        """INSERT INTO user_accounts (email, oauth_sub, full_name, role_id, account_status)
           VALUES (%s, %s, %s, %s, 'active')
           ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
           RETURNING user_id""",
        (SEED_LIBRARIAN_EMAIL, "seed_books_oauth", "Seed Books Librarian", role_id),
    )
    return cur.fetchone()[0]


def ensure_departments(cur):
    for name in PROGRAMS:
        cur.execute(
            """INSERT INTO departments (name, dept_type) VALUES (%s, 'program')
               ON CONFLICT DO NOTHING""",
            (name,),
        )


def reset_seed(cur):
    """Delete ONLY rows created by this seeder: accessions belonging to
    [SEED-BOOKS] titles (whatever their number format), then catalog rows
    left with no copies."""
    cur.execute(
        """SELECT a.accession_id FROM accession_log a
           JOIN book_catalog b ON b.book_id = a.book_id
           WHERE b.description LIKE %s""",
        ("%" + SEED_MARKER + "%",),
    )
    aids = [r[0] for r in cur.fetchall()]
    if aids:
        cur.execute(
            "DELETE FROM circulation_records WHERE accession_id = ANY(%s)", (aids,)
        )
        print("removed %d seeded circulation rows" % cur.rowcount)
        cur.execute(
            "DELETE FROM inventory_status WHERE accession_id = ANY(%s)", (aids,)
        )
        print("removed %d seeded inventory rows" % cur.rowcount)
        cur.execute(
            "DELETE FROM accession_log WHERE accession_id = ANY(%s)", (aids,)
        )
        print("removed %d seeded accession rows" % cur.rowcount)
    cur.execute(
        """DELETE FROM book_catalog b
           WHERE b.description LIKE %s
             AND NOT EXISTS (SELECT 1 FROM accession_log a
                             WHERE a.book_id = b.book_id)""",
        ("%" + SEED_MARKER + "%",),
    )
    print("removed %d orphaned seeded catalog rows" % cur.rowcount)


def _next_accession_seq(cur, prefix):
    """Next free sequence number: max(numeric suffix)+1 over accession
    numbers matching this run's format, so reruns never reuse a number."""
    cur.execute("SELECT accession_number FROM accession_log")
    pattern = re.compile(r"^%s(\d+)$" % re.escape(prefix))
    best = 0
    for (acc_no,) in cur.fetchall():
        m = pattern.match(acc_no or "")
        if m:
            best = max(best, int(m.group(1)))
    return best + 1


def _seeded_copy_counts(cur):
    """Existing copy count per [SEED-BOOKS] title."""
    cur.execute(
        """SELECT a.book_id, COUNT(*)
           FROM accession_log a
           JOIN book_catalog b ON b.book_id = a.book_id
           WHERE b.description LIKE %s
           GROUP BY a.book_id""",
        ("%" + SEED_MARKER + "%",),
    )
    return dict(cur.fetchall())


def seed(conn, target, prefix=""):
    cur = conn.cursor()
    ensure_departments(cur)
    librarian_id = ensure_seed_librarian(cur)

    entries = list(flatten_books())
    planned = sum(e[7] for e in entries)

    # Guarantee the copy target regardless of hand-counted arithmetic:
    # round-robin extra copies onto multi-copy titles (single-copy
    # references stay at exactly 1). Spreads evenly so core titles gain
    # a few copies each and the distribution stays plausible.
    entries = [list(e) for e in entries]
    multi_idx = [i for i, e in enumerate(entries) if e[7] >= 2]
    extra = max(0, target - planned)
    k = 0
    while extra > 0 and multi_idx:
        entries[multi_idx[k % len(multi_idx)]][7] += 1
        extra -= 1
        k += 1

    # Cache existing books by natural key.
    cur.execute("SELECT book_id, title, author, isbn FROM book_catalog")
    book_by_key = {(t, a, i): bid for bid, t, a, i in cur.fetchall()}

    titles_new = titles_reused = copies_new = copies_skipped = 0
    per_program = {p: [0, 0] for p in PROGRAMS}  # books, copies (new this run)
    for n, (program, title, author, edition, publisher, year,
            subject, copies, blurb) in enumerate(entries):
        isbn = isbn13_for(n)
        key = (title, author, isbn)
        book_id = book_by_key.get(key)
        if book_id is None:
            # Same dedup rule as the cataloging add-book flow
            # (get_book_by_title_author_isbn): title + author + isbn.
            cur.execute(
                """INSERT INTO book_catalog
                   (title, author, edition, publisher, year_published,
                    subject_classification, call_number, isbn, material_type,
                    description, catalog_status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Book', %s, 'active')
                   RETURNING book_id""",
                (title, author, edition, publisher, year, subject,
                 call_number_for(program, n, year), isbn,
                 "%s Recommended for %s. %s"
                 % (blurb, PROGRAM_LABEL[program], SEED_MARKER)),
            )
            book_id = cur.fetchone()[0]
            book_by_key[key] = book_id
            titles_new += 1
        else:
            titles_reused += 1
        per_program[program][0] += 1

    # Top up each seeded title to its planned copy count, numbering new
    # copies sequentially from max(existing)+1 (0001, 0002, ... on a fresh
    # DB). Reruns only fill shortfalls — never duplicates.
    have = _seeded_copy_counts(cur)  # includes titles inserted above
    seq = _next_accession_seq(cur, prefix)
    cur.execute("SELECT accession_number FROM accession_log")
    existing_acc = {r[0] for r in cur.fetchall()}
    for n, (program, title, author, edition, publisher, year,
            subject, copies, blurb) in enumerate(entries):
        book_id = book_by_key[(title, author, isbn13_for(n))]
        missing = copies - have.get(book_id, 0)
        copies_skipped += copies - max(missing, 0)
        for c in range(max(missing, 0)):
            acc_no = "%s%04d" % (prefix, seq)
            seq += 1
            while acc_no in existing_acc:
                acc_no = "%s%04d" % (prefix, seq)
                seq += 1
            source = "donation" if (n + c) % 7 == 0 else "purchase"
            try:
                cur.execute(
                    """INSERT INTO accession_log
                       (accession_number, book_id, librarian_id, source)
                       VALUES (%s, %s, %s, %s)""",
                    (acc_no, book_id, librarian_id, source),
                )
            except Exception:
                # Another concurrent run won the race on this number.
                conn.rollback()
                copies_skipped += 1
                continue
            existing_acc.add(acc_no)
            copies_new += 1
            per_program[program][1] += 1

    conn.commit()

    # ---- verification + report -----------------------------------------
    cur.execute("SELECT COUNT(*) FROM book_catalog")
    total_titles = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM accession_log")
    total_copies = cur.fetchone()[0]
    cur.execute(
        """SELECT COUNT(*) FROM accession_log a
           JOIN book_catalog b ON b.book_id = a.book_id
           WHERE b.description LIKE %s""",
        ("%" + SEED_MARKER + "%",),
    )
    seeded_copies = cur.fetchone()[0]
    cur.execute(
        """SELECT b.book_id, b.subject_classification,
                  (SELECT COUNT(*) FROM accession_log a
                   WHERE a.book_id = b.book_id)
           FROM book_catalog b WHERE b.description LIKE %s""",
        ("%" + SEED_MARKER + "%",),
    )
    seeded_rows = cur.fetchall()
    # Attribute seeded rows back to programs via subject match.
    cur.close()
    return {
        "titles_new": titles_new,
        "titles_reused": titles_reused,
        "copies_new": copies_new,
        "copies_skipped": copies_skipped,
        "per_program": per_program,
        "total_titles": total_titles,
        "total_copies": total_copies,
        "seeded_copies": seeded_copies,
        "seeded_titles": len(seeded_rows),
    }


def main():
    ap = argparse.ArgumentParser(description="Seed 5000+ book copies.")
    ap.add_argument("--dsn", default=None,
                    help="Postgres connection string "
                         "(falls back to DATABASE_URL from .env)")
    ap.add_argument("--target", type=int, default=TARGET_COPIES,
                    help="Minimum physical copies (default %d)" % TARGET_COPIES)
    ap.add_argument("--reset", action="store_true",
                    help="Delete prior seeded rows before seeding")
    ap.add_argument("--prefix", default="",
                    help="Accession-number prefix (default: none, i.e. "
                         "0001, 0002, ...). Use --prefix BKSEED- for the "
                         "old prefixed scheme.")
    args = ap.parse_args()

    conn = get_conn(args.dsn)
    try:
        ensure_schema(conn)
        if args.reset:
            cur = conn.cursor()
            reset_seed(cur)
            conn.commit()
            cur.close()
        report = seed(conn, args.target, args.prefix)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("\n=== Book seeder report ===")
    print("titles inserted: %d | titles reused: %d"
          % (report["titles_new"], report["titles_reused"]))
    print("copies inserted: %d | copies skipped (already present): %d"
          % (report["copies_new"], report["copies_skipped"]))
    print("seeded titles: %d | seeded copies: %d"
          % (report["seeded_titles"], report["seeded_copies"]))
    print("DB totals: %d titles, %d copies"
          % (report["total_titles"], report["total_copies"]))
    print("\nPer program (titles handled / copies added this run):")
    for program in PROGRAMS:
        books, copies = report["per_program"][program]
        print("  %-40s titles=%3d copies=%4d" % (program, books, copies))
    if report["total_copies"] < args.target:
        sys.exit("WARNING: total copies %d below target %d"
                 % (report["total_copies"], args.target))
    print("\nOK: total physical copies >= %d" % args.target)


if __name__ == "__main__":
    main()
