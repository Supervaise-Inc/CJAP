# B1 intake report: books (batch-04)

Run 23 Sep 2026. Input: the 8 confirmed `book_split/*/split_plan.csv` files. The team confirmed all 8 as-is and chose to keep long chapters whole for now.

**Result: 167 book-chapter rows appended to `intake_manifest.csv`**, one per CHAPTER row. None were added for SKIP parts, and no chapter was withheld as a duplicate. The manifest now has 186 rows: 19 earlier column rows and 167 book chapters. A backup of the manifest from before this run is in `intake_manifest.backup_pre-B1_2026-09-23.csv`.

**Books partly in the corpus.** None of the 8 books is one of the partly-loaded ones (A Centenary of Justice, Bio-Age, Justice and Faith, With Due Respect). The retired Centenary IDs BA040, BC009, BC010 and BD018 stay retired and are not affected.

## IDs used
Next-free IDs were re-checked against corpus/ (1,104 docs), the manifest and retired_doc_ids.csv, and they matched the register: BA051 · BB009 · BC023 · BD027 · BE030.

Books were taken in order of publication (1994 → 2006), and chapters in book order within each book, so each theme series runs chronologically.

| Series | Range used | Count | Next free after B1 |
|---|---|---|---|
| BA | BA051–BA107 | 57 | BA108 |
| BB | BB009–BB044 | 36 | BB045 |
| BC | BC023–BC046 | 24 | BC047 |
| BD | BD027–BD071 | 45 | BD072 |
| BE | BE030–BE034 | 5 | BE035 |

## Chapters per book
| Book | Chapters | A | B | C | D | E |
|---|---|---|---|---|---|---|
| Love God, Serve Man | 22 | 2 | 4 | 14 | 1 | 1 |
| Battles in the Supreme Court | 11 | 6 | 2 | 0 | 3 | 0 |
| Leadership by Example: The Davide Standard | 14 | 7 | 2 | 1 | 4 | 0 |
| Transparency, Unanimity & Diversity | 24 | 11 | 7 | 3 | 3 | 0 |
| Reforming the Judiciary | 20 | 7 | 3 | 2 | 8 | 0 |
| Leveling the Playing Field | 20 | 9 | 4 | 0 | 3 | 4 |
| Judicial Renaissance | 21 | 4 | 6 | 1 | 10 | 0 |
| Liberty and Prosperity | 35 | 11 | 8 | 3 | 13 | 0 |

Theme letters follow the practice already used in corpus/books:
- **A**: constitutional, criminal and election law, and rights.
- **B**: economy, business, labor and property.
- **C**: faith, values, personal pieces and tributes.
- **D**: judicial reform, court administration, the legal profession, and the liberty-and-prosperity (FLP) philosophy. Existing BD rows cover the APJR, mediation, the JBC and PhilJA.
- **E**: current-events and bio-age/technology commentary.

Every row carries a one-line `theme_reason`. **Please review the themes, especially the judgment calls:**
- Battles Ch. 2 and 11: D rather than A.
- LGSM Ch. 8 (Church in politics): C rather than E.
- LGSM Ch. 15 (peace process): E.
- JR Ch. 11 and L&P Ch. 4 (the liberty-and-prosperity philosophy): D.
- LPF Ch. 10–14 (bio-age): E, except Ch. 12, which is D.

### Love God, Serve Man
| Ch. | doc_id | Theme | Date (precision) | Title |
|---|---|---|---|---|
| 1 | BC023 | C | 1990-07-12 (day) | Ch. 1: Love God, Serve Man |
| 2 | BC024 | C | 1991-06-27 (day) | Ch. 2: A Year of Love and Service |
| 3 | BC025 | C | 1994-01-01 (year) | Ch. 3: ‘Salamat Po’ |
| 4 | BD027 | D | 1992-10-17 (day) | Ch. 4: On Improving the Administration of Justice |
| 5 | BB009 | B | 1993-10-27 (day) | Ch. 5: Legal Problems in International Trade Spawned by the AFTA |
| 6 | BA051 | A | 1987-01-14 (day) | Ch. 6: Does the MNLF Have International Legal Personality? |
| 7 | BA052 | A | 1994-02-01 (day) | Ch. 7: Legal Consequences of “Part-time” Service to the Government |
| 8 | BC026 | C | 1992-03-11 (day) | Ch. 8: Why is the Catholic Church in Politics? |
| 9 | BC027 | C | 1994-02-23 (day) | Ch. 9: Bukas Loob sa Diyos: Called to Evangelize |
| 10 | BC028 | C | 1994-01-01 (year) | Ch. 10: Lord, I Am Your Servant |
| 11 | BC029 | C | 1992-11-27 (day) | Ch. 11: Lay Empowerment in Building a Community of Believers |
| 12 | BC030 | C | 1991-05-19 (day) | Ch. 12: PCP II's Aspirations for Our Faithful |
| 13 | BB010 | B | 1985-11-15 (day) | Ch. 13: A Salute to ASTA |
| 14 | BB011 | B | 1988-02-28 (day) | Ch. 14: Investment Prospects in Philippine Tourism |
| 15 | BE030 | E | 1992-11-03 (day) | Ch. 15: Peace is Everyone's Concern |
| 16 | BB012 | B | 1994-03-15 (day) | Ch. 16: Three Perspectives on the Role of Filipino Values in Economic Development |
| 17 | BC031 | C | 1988-11-17 (day) | Ch. 17: A Plea for Honesty |
| 18 | BC032 | C | 1991-04-04 (day) | Ch. 18: An Easter Message to Rotary |
| 19 | BC033 | C | 1991-01-03 (day) | Ch. 19: A New Year's Wish |
| 20 | BC034 | C | 1994-01-01 (year) | Ch. 20: Some Prayers and Invocations |
| 21 | BC035 | C | 1992-05-19 (day) | Ch. 21: God's Commandment of Love |
| 22 | BC036 | C | 1994-01-01 (year) | Ch. 22: Introductions |

### Battles in the Supreme Court
| Ch. | doc_id | Theme | Date (precision) | Title |
|---|---|---|---|---|
| 1 | BD028 | D | 1998-11-01 (month) | Ch. 1: A WINDOW TO THE COURT |
| 2 | BD029 | D | 1998-11-01 (month) | Ch. 2: Prologue to THE COURT BATTLES |
| 3 | BA053 | A | 1998-11-01 (month) | Ch. 3: THE "CHA-CHA" BATTLES |
| 4 | BA054 | A | 1998-11-01 (month) | Ch. 4: BATTLES OVER LIFE AND DEATH |
| 5 | BA055 | A | 1998-11-01 (month) | Ch. 5: BATTLES OVER THE PEOPLE’S SOVEREIGNTY |
| 6 | BB013 | B | 1998-11-01 (month) | Ch. 6: BATTLES ON THE ECONOMIC FRONT |
| 7 | BA056 | A | 1998-11-01 (month) | Ch. 7: OTHER CONSTITUTIONAL BATTLES |
| 8 | BB014 | B | 1998-11-01 (month) | Ch. 8: BATTLES OVER THE RIGHTS OF LABOR |
| 9 | BA057 | A | 1998-11-01 (month) | Ch. 9: BATTLES OF THE DAMNED |
| 10 | BA058 | A | 1998-11-01 (month) | Ch. 10: BATTLES OVER CIVIL RIGHTS |
| 11 | BD030 | D | 1998-11-01 (month) | Ch. 11: Epilogue: THE REAL VICTORY |

### Leadership by Example: The Davide Standard
| Ch. | doc_id | Theme | Date (precision) | Title |
|---|---|---|---|---|
| 1 | BD031 | D | 1999-01-01 (year) | Ch. 1: Conscience of Society |
| 2 | BD032 | D | 1999-01-01 (year) | Ch. 2: A Friendly Court |
| 3 | BD033 | D | 1999-01-01 (year) | Ch. 3: Attributes of a Good Judge |
| 4 | BC037 | C | 1999-01-01 (year) | Ch. 4: Chief Justice Davide: An Introduction |
| 5 | BD034 | D | 1999-01-01 (year) | Ch. 5: Setting the Standards |
| 6 | BA059 | A | 1999-01-01 (year) | Ch. 6: The Death Penalty Law: The Debate Continues |
| 7 | BA060 | A | 1999-01-01 (year) | Ch. 7: Warrantless Arrests and Seizures Revisited |
| 8 | BA061 | A | 1999-01-01 (year) | Ch. 8: Effect of a Void Warrant of Arrest on Jurisdiction Over the Accused |
| 9 | BB015 | B | 1999-01-01 (year) | Ch. 9: Invoking the National Interest in a Labor Dispute |
| 10 | BB016 | B | 1999-01-01 (year) | Ch. 10: Civil Servants’ Right to Compensation During Preventive Suspension |
| 11 | BA062 | A | 1999-01-01 (year) | Ch. 11: Common Meaning of Common Words in the Constitution |
| 12 | BA063 | A | 1999-01-01 (year) | Ch. 12: Counting Automated Ballots: Which Rules Apply? |
| 13 | BA064 | A | 1999-01-01 (year) | Ch. 13: Upholding Popular Sovereignty in Election Cases |
| 14 | BA065 | A | 1999-01-01 (year) | Ch. 14: The Power of the Supreme Court to Review Internal Acts of Congress |

### Transparency, Unanimity & Diversity
| Ch. | doc_id | Theme | Date (precision) | Title |
|---|---|---|---|---|
| 1 | BD035 | D | 2000-11-01 (month) | Ch. 1: Problems and Solutions |
| 2 | BD036 | D | 2000-11-01 (month) | Ch. 2: Judicial Reform Is Also the Business of Business |
| 3 | BD037 | D | 2000-11-01 (month) | Ch. 3: Microchips, Modems and Media Invade Mount Olympus |
| 4 | BC038 | C | 2000-11-01 (month) | Ch. 4: Paradigms Change But Values Endure |
| 5 | BC039 | C | 2000-11-01 (month) | Ch. 5: Excellence Is Not Enough |
| 6 | BC040 | C | 2000-11-01 (month) | Ch. 6: e-Values for the e-Age and Beyond |
| 7 | BB017 | B | 2000-11-01 (month) | Ch. 7: Ty v. Trampe: Validity of Increases in Real Estate Taxes |
| 8 | BB018 | B | 2000-11-01 (month) | Ch. 8: First Philippine International Bank v. Court of Appeals: Honoring a Perfected Contract |
| 9 | BB019 | B | 2000-11-01 (month) | Ch. 9: The PCGG Cases: Recovery of Ill-Gotten Wealth |
| 10 | BB020 | B | 2000-11-01 (month) | Ch. 10: Tañada v. Angara: The Advent of Globalization in the Philippines |
| 11 | BB021 | B | 2000-11-01 (month) | Ch. 11: The NLRC Cases: Finding the Right Balance Between Labor and Management |
| 12 | BA066 | A | 2000-11-01 (month) | Ch. 12: Republic v. Molina: Setting the Procedure for Nullifying a Marriage |
| 13 | BA067 | A | 2000-11-01 (month) | Ch. 13: Obosa v. Court of Appeals: Authority to Approve Bail Bonds in Appealed Cases |
| 14 | BA068 | A | 2000-11-01 (month) | Ch. 14: Cabaero v. Cantos: May an Answer With Counterclaim Be Filed in a Criminal Case? |
| 15 | BA069 | A | 2000-11-01 (month) | Ch. 15: Ho v. People: Basis for Arrest Warrant |
| 16 | BA070 | A | 2000-11-01 (month) | Ch. 16: Death Penalty Cases: A Moratorium on Death |
| 17 | BB022 | B | 2000-11-01 (month) | Ch. 17: Serrano v. NLRC: Are Workers Entitled to Due Process Prior to Dismissal? |
| 18 | BA071 | A | 2000-11-01 (month) | Ch. 18: Secretary of Justice v. Lantion and Jimenez: Due Process in Extradition Cases |
| 19 | BA072 | A | 2000-11-01 (month) | Ch. 19: Veterans Federation Party v. Comelec The Party-List System — a Disagreement on Mathematics |
| 20 | BA073 | A | 2000-11-01 (month) | Ch. 20: ABS-CBN v. Comelec: Exit Polls — a New Paradigm of Free Expression |
| 21 | BA074 | A | 2000-11-01 (month) | Ch. 21: Pimentel v. Aguirre: Upholding the Fiscal Autonomy of Local Government Units |
| 22 | BB023 | B | 2000-11-01 (month) | Ch. 22: Firestone Ceramics v. Court of Appeals: Sauce for the Poor Goose and the Rich Gander |
| 23 | BA075 | A | 2000-11-01 (month) | Ch. 23: Basher v. Comelec: Resolving “Insignificant Cases” |
| 24 | BA076 | A | 2000-11-01 (month) | Ch. 24: Mercado v. Tan: Is a Judicial Declaration of Nullity of a Prior Marriage Needed to Abate Bigamy? |

### Reforming the Judiciary
| Ch. | doc_id | Theme | Date (precision) | Title |
|---|---|---|---|---|
| 1 | BD038 | D | 2002-12-01 (month) | Ch. 1: An Introduction to the APJR |
| 3 | BD039 | D | 2002-12-01 (month) | Ch. 3: Battling Corruption, Incompetence and Delay |
| 4 | BD040 | D | 2002-12-01 (month) | Ch. 4: Prerequisites for a Successful Reform Program |
| 5 | BD041 | D | 2002-12-01 (month) | Ch. 5: Good Governance Begins with Ethics |
| 6 | BA077 | A | 2002-12-01 (month) | Ch. 6: Rotarians Defend the Rule of Law |
| 7 | BD042 | D | 2002-12-01 (month) | Ch. 7: Transparency, the Key to Sound Judgments |
| 8 | BD043 | D | 2002-12-01 (month) | Ch. 8: The Moot Court — a Virtual Legal Reality |
| 9 | BD044 | D | 2002-12-01 (month) | Ch. 9: A Centennial Toast to Justice and Justices |
| 11 | BA078 | A | 2002-12-01 (month) | Ch. 11: Saving the Constitutional System |
| 12 | BC041 | C | 2002-12-01 (month) | Ch. 12: What I Learned at Far Eastern University |
| 13 | BC042 | C | 2002-04-06 (day) | Ch. 13: A Tribute to Valedictorians |
| 14 | BA079 | A | 2002-12-01 (month) | Ch. 14: An Emerging Paradigm of Free Expression |
| 15 | BD045 | D | 2002-12-01 (month) | Ch. 15: Postscript to A Centenary of Justice |
| 16 | BA080 | A | 2002-12-01 (month) | Ch. 16: Estrada v. Sandiganbayan: The Anti-Plunder Law Is Constitutional |
| 17 | BB024 | B | 2002-12-01 (month) | Ch. 17: Republic v. Cocofed: Coco Levies Are Prima Facie Public Funds |
| 18 | BA081 | A | 2002-12-01 (month) | Ch. 18: Lim v. Executive Secretary: Cases Are Not Decided on Hypothetical Assumptions |
| 19 | BB025 | B | 2002-12-01 (month) | Ch. 19: Equatorial Reality v. Mayfair Theater: General Principles Do Not Decide Specific Cases |
| 20 | BB026 | B | 2002-12-01 (month) | Ch. 20: Makati City v. Civil Service Commission: Are Government Employees Entitled to an 'Automatic' Leave of Absence? |
| 21 | BA082 | A | 2002-12-01 (month) | Ch. 21: Government of the United States v. Purganan: Extradition and the Right to Bail |
| 22 | BA083 | A | 2002-12-01 (month) | Ch. 22: Important Developments on the Death Penalty |

### Leveling the Playing Field
| Ch. | doc_id | Theme | Date (precision) | Title |
|---|---|---|---|---|
| 1 | BA084 | A | 2004-12-01 (month) | Ch. 1: Judicial Activism in the Philippines |
| 2 | BB027 | B | 2004-12-01 (month) | Ch. 2: Role of the Supreme Court in Economic Development |
| 3 | BB028 | B | 2004-12-01 (month) | Ch. 3: Not Only Prosperity, But Also Peace |
| 4 | BB029 | B | 2004-12-01 (month) | Ch. 4: Gravely Abusive Contracts |
| 5 | BB030 | B | 2004-12-01 (month) | Ch. 5: Protecting the Consumers |
| 6 | BD046 | D | 2004-12-01 (month) | Ch. 6: Q & A During the “Chamber-to-Chamber” Dialogues |
| 7 | BA085 | A | 2004-12-01 (month) | Ch. 7: A Unique Mode of Nurturing Democracy |
| 8 | BD047 | D | 2004-12-01 (month) | Ch. 8: The Judiciary and Media: Natural Partners in Our Democracy |
| 10 | BE031 | E | 2004-03-01 (month) | Ch. 10: Borderless Justice |
| 11 | BE032 | E | 2004-03-01 (month) | Ch. 11: Judicial Excellence in the Bio-Age |
| 12 | BD048 | D | 2004-03-01 (month) | Ch. 12: Case Management of Bio-Litigations in the Philippines |
| 13 | BE033 | E | 2004-03-01 (month) | Ch. 13: Law and the Biosciences in Asia |
| 14 | BE034 | E | 2004-03-01 (month) | Ch. 14: Ethics in the Biotechnological Revolution |
| 15 | BA086 | A | 2004-12-01 (month) | Ch. 15: Francisco v. House of Representatives: Constitutionality of the Davide Impeachment |
| 16 | BA087 | A | 2004-12-01 (month) | Ch. 16: Information Technology Foundation v. Comelec: Flawed Contract for Election Automation |
| 17 | BA088 | A | 2004-12-01 (month) | Ch. 17: People v. Genosa: The Battered Woman Syndrome |
| 18 | BA089 | A | 2004-12-01 (month) | Ch. 18: Sanlakas v. Executive Secretary: Constitutionality of a “State of Rebellion” |
| 19 | BA090 | A | 2004-12-01 (month) | Ch. 19: Velarde v. Social Justice Party: Form and Substance of Judicial Decisions |
| 20 | BA091 | A | 2004-12-01 (month) | Ch. 20: Romualdez v. Sandiganbayan: Constitutionality of the Anti-Graft Law |
| 21 | BA092 | A | 2004-12-01 (month) | Ch. 21: New Jurisprudence on Capital Offenses |

### Judicial Renaissance
| Ch. | doc_id | Theme | Date (precision) | Title |
|---|---|---|---|---|
| 1 | BD049 | D | 2005-11-01 (month) | Ch. 1: A Transformed Judiciary |
| 2 | BD050 | D | 2005-11-01 (month) | Ch. 2: The APJR: An Executive Summary |
| 3 | BD051 | D | 2005-11-01 (month) | Ch. 3: Global Support for Judicial Reforms |
| 5 | BD052 | D | 2005-11-01 (month) | Ch. 5: A Celebration of Thanksgiving |
| 6 | BD053 | D | 2005-11-01 (month) | Ch. 6: Holmes, Money and Trust |
| 7 | BA093 | A | 2005-11-01 (month) | Ch. 7: Independence and Integrity of the Philippine Judiciary |
| 8 | BB031 | B | 2005-11-01 (month) | Ch. 8: Access to Justice: A Prerequisite to Economic Development |
| 9 | BD054 | D | 2005-11-01 (month) | Ch. 9: Judging the Judges |
| 10 | BD055 | D | 2005-11-01 (month) | Ch. 10: Beyond Excellence |
| 11 | BD056 | D | 2005-11-01 (month) | Ch. 11: Liberty and Prosperity |
| 12 | BD057 | D | 2005-11-01 (month) | Ch. 12: An Ethical Compass for the Legal Profession |
| 13 | BC043 | C | 2005-11-01 (month) | Ch. 13: The Power of Example |
| 14 | BB032 | B | 2005-02-01 (month) | Ch. 14: Invest in the Whole Country, Not Just in the Mining Industry |
| 15 | BB033 | B | 2005-11-01 (month) | Ch. 15: La Bugal B’laan v. Ramos: The Constitutionality of the Mining Law |
| 16 | BB034 | B | 2005-11-01 (month) | Ch. 16: Abakada Guro Partylist v. Ermita: The Constitutionality of the E-Vat Law |
| 17 | BB035 | B | 2005-11-01 (month) | Ch. 17: Southern Cross Cement Corporation v. Philippine Cement Manufacturers Corporation: Executive Power to Protect Local Industries |
| 18 | BA094 | A | 2005-11-01 (month) | Ch. 18: Central Bank Employees Association v. Monetary Board: Constitutionality of Increases in CB Employees’ Compensation |
| 19 | BB036 | B | 2005-11-01 (month) | Ch. 19: Agabon v. NLRC: Sanctions for Violation of Due Process in Labor Cases |
| 20 | BD058 | D | 2005-11-01 (month) | Ch. 20: Presidential Commission on Good Government v. Sandiganbayan: Ethical Conduct of a Lawyer |
| 21 | BA095 | A | 2005-11-01 (month) | Ch. 21: Information Technology Foundation of the Philippines v. Comelec: The Use of ACMs in the ARMM Elections: A Reprise |
| 22 | BA096 | A | 2005-11-01 (month) | Ch. 22: The HRET at Work |

### Liberty and Prosperity
| Ch. | doc_id | Theme | Date (precision) | Title |
|---|---|---|---|---|
| 1 | BC044 | C | 2006-01-01 (year) | Ch. 1: The 21st Chief Justice of the Philippines |
| 2 | BC045 | C | 2006-01-01 (year) | Ch. 2: Humble Beginnings |
| 3 | BD059 | D | 2006-01-01 (year) | Ch. 3: Jurist and Leader |
| 4 | BD060 | D | 2006-01-01 (year) | Ch. 4: Twin Beacons for the Judiciary |
| 5 | BD061 | D | 2006-01-01 (year) | Ch. 5: Nominating the Best and the Brightest |
| 6 | BD062 | D | 2006-01-01 (year) | Ch. 6: A Revitalized Legal Profession |
| 7 | BD063 | D | 2006-01-01 (year) | Ch. 7: A School Par Excellence for Judges |
| 8 | BC046 | C | 2006-01-01 (year) | Ch. 8: E-Values for the Filipino Youth |
| 9 | BB037 | B | 2006-01-01 (year) | Ch. 9: Civil Society's Role in Promoting Democracy and Development |
| 10 | BD064 | D | 2006-01-01 (year) | Ch. 10: Addressing the ACID Problems of the Philippine Judiciary |
| 11 | BD065 | D | 2006-01-01 (year) | Ch. 11: Digitizing Law Schools |
| 12 | BD066 | D | 2006-01-01 (year) | Ch. 12: The Challenge of ADR |
| 13 | BD067 | D | 2006-01-01 (year) | Ch. 13: Ensuring the Success of the Philippine Judicial Reform Program |
| 14 | BD068 | D | 2006-01-01 (year) | Ch. 14: Engendering the Judiciary |
| 15 | BB038 | B | 2006-01-01 (year) | Ch. 15: The Judiciary and the Economy |
| 16 | BD069 | D | 2006-06-21 (day) | Ch. 16: Maximum Benefits for All Judicial Employees |
| 17 | BD070 | D | 2006-01-01 (year) | Ch. 17: Achieving Judicial Goals the Rotary Way |
| 18 | BA097 | A | 2006-01-01 (year) | Ch. 18: Anchoring the Ship of State |
| 19 | BA098 | A | 2006-01-01 (year) | Ch. 19: The Senate v. Ermita: Validity of EO 464 Barring Executive Officials from Appearing in Congress |
| 20 | BA099 | A | 2006-01-01 (year) | Ch. 20: Bayan Muna v. Ermita: Validity of the Calibrated Preemptive Response (CPR) Policy |
| 21 | BA100 | A | 2006-01-01 (year) | Ch. 21: David v. Arroyo: Constitutionality of Proclaiming a State of National Emergency |
| 22 | BA101 | A | 2006-01-01 (year) | Ch. 22: KMU v. The Director General (NEDA): Validity of the Executive ID System |
| 23 | BA102 | A | 2006-01-01 (year) | Ch. 23: Lumanlaw v. Peralta: Violation of the Right to Speedy Trial |
| 24 | BA103 | A | 2006-01-01 (year) | Ch. 24: Silahis v. Soluta: Liability of Private Persons Conducting Unreasonable Searches |
| 25 | BA104 | A | 2006-01-01 (year) | Ch. 25: Estrada v. Escritor: Religious Freedom as a Defense in Concubinage |
| 26 | BB039 | B | 2006-01-01 (year) | Ch. 26: Abacus v. Ampil: Liabilities of a Stock Market Investor |
| 27 | BB040 | B | 2006-01-01 (year) | Ch. 27: Didipio v. Gozun: Constitutionality of the Mining Act: A Reprise |
| 28 | BB041 | B | 2006-01-01 (year) | Ch. 28: Manila International Airport Authority v. City of Parañaque: The Power of Local Governments to Tax National Government Instrumentalities |
| 29 | BD071 | D | 2006-01-01 (year) | Ch. 29: Velez v. De Vera: Succession to the IBP Presidency |
| 30 | BA105 | A | 2006-01-01 (year) | Ch. 30: Rufino v. Endriga: Does the President Have the Power to Appoint CCP Trustees? |
| 31 | BB042 | B | 2006-01-01 (year) | Ch. 31: Yuchengco v. Sandiganbayan: Ownership of Sequestered PLDT Shares |
| 32 | BA106 | A | 2006-01-01 (year) | Ch. 32: Mirasol v. DPWH: Regulation of Traffic on Tollways |
| 33 | BA107 | A | 2006-01-01 (year) | Ch. 33: Hernandez v. Napocor: Injunction Against High-Voltage Lines Adjacent to Residences |
| 34 | BB043 | B | 2006-01-01 (year) | Ch. 34: Coastal Pacific Trading v. Southern Rolling Mills: Directors' Duty of Loyalty and Fidelity to Creditors |
| 35 | BB044 | B | 2006-01-01 (year) | Ch. 35: Nasecore v. Energy Regulatory Commission: Publication of Applications for Rate Adjustments - an Indispensable Requirement of Due Process |

## Duplicate check
Two checks were run:
- The normalised titles of all 167 chapters were compared with every corpus/*/*/*.json title and with archive/phase1/id_map_phase1_to_live.csv.
- The full texts were compared with all 1,104 `data/text` bodies, using 8-word shingle overlap. For collected pieces, the original date was also compared with the columns and speeches.

**No chapter is a duplicate, so none was withheld.** Every title match turned out to be a different text:
| Chapter | Corpus match | Finding |
|---|---|---|
| LPF Ch. 1 Judicial Activism in the Philippines (BA084) | column CA111, same title (2023-04-10) | text overlap ≈0%, a later column |
| L&P Ch. 7 A School Par Excellence for Judges (BD063) | speech SD137, same title (2006-11-30) | text overlap ≈0%, a different PhilJA address |
| TUD Ch. 22 Firestone Ceramics (BB023) | Centenary BD017 "… A Postscript" | the corpus piece is a later postscript to this chapter |
| L&P Ch. 1 The 21st Chief Justice (BC044) | biography GC033 (similar title); WDR BD002 | different authors and texts |
| LGSM Ch. 1 Love God, Serve Man (BC023) | biography GC009, same heading | GC009 is the biographer's narrative about this speech |

Partial text overlaps, noted in the rows and not duplicates:
- TUD Ch. 12 (BA066): about 28% of its text reappears in Bio-Age BA048.
- Column CA144: reuses about 31% of L&P Ch. 20 (BA099).
- LBE Ch. 1 (BD031): about 17% phrase overlap with columns CA103 and CA402.

The corpus speeches start in November 1994, so none of LGSM's 1985–1994 pieces can be in them, and none of the dated collected pieces matched a speech or column by date.

## Long chapters: kept whole (team decision), split still possible before IDs are final
There are 21 rows flagged "long" (over 6,000 words). If any is split later, it becomes "<Book> -- Ch. N.n: <Section>" with consecutive IDs, and the IDs after it in that series would shift. **Decide before the team confirms the IDs.**

| doc_id | Chapter | Words |
|---|---|---|
| BD028 | Battles in the Supreme Court -- Ch. 1: A WINDOW TO THE COURT | 7747 |
| BB013 | Battles in the Supreme Court -- Ch. 6: BATTLES ON THE ECONOMIC FRONT | 6380 |
| BA057 | Battles in the Supreme Court -- Ch. 9: BATTLES OF THE DAMNED | 9842 |
| BD034 | Leadership by Example: The Davide Standard -- Ch. 5: Setting the Standards | 10744 |
| BA059 | Leadership by Example: The Davide Standard -- Ch. 6: The Death Penalty Law: The Debate Continues | 9706 |
| BA063 | Leadership by Example: The Davide Standard -- Ch. 12: Counting Automated Ballots: Which Rules Apply? | 9948 |
| BA070 | Transparency, Unanimity & Diversity -- Ch. 16: Death Penalty Cases: A Moratorium on Death | 8794 |
| BB022 | Transparency, Unanimity & Diversity -- Ch. 17: Serrano v. NLRC: Are Workers Entitled to Due Process Prior to Dismissal? | 10638 |
| BA072 | Transparency, Unanimity & Diversity -- Ch. 19: Veterans Federation Party v. Comelec The Party-List System — a Disagreement on Mathematics | 7173 |
| BA080 | Reforming the Judiciary -- Ch. 16: Estrada v. Sandiganbayan: The Anti-Plunder Law Is Constitutional | 8480 |
| BA082 | Reforming the Judiciary -- Ch. 21: Government of the United States v. Purganan: Extradition and the Right to Bail | 10677 |
| BA083 | Reforming the Judiciary -- Ch. 22: Important Developments on the Death Penalty | 6201 |
| BA086 | Leveling the Playing Field -- Ch. 15: Francisco v. House of Representatives: Constitutionality of the Davide Impeachment | 10326 |
| BA087 | Leveling the Playing Field -- Ch. 16: Information Technology Foundation v. Comelec: Flawed Contract for Election Automation | 9748 |
| BA092 | Leveling the Playing Field -- Ch. 21: New Jurisprudence on Capital Offenses | 7025 |
| BD049 | Judicial Renaissance -- Ch. 1: A Transformed Judiciary | 6668 |
| BB033 | Judicial Renaissance -- Ch. 15: La Bugal B’laan v. Ramos: The Constitutionality of the Mining Law | 11280 |
| BB034 | Judicial Renaissance -- Ch. 16: Abakada Guro Partylist v. Ermita: The Constitutionality of the E-Vat Law | 6577 |
| BB035 | Judicial Renaissance -- Ch. 17: Southern Cross Cement Corporation v. Philippine Cement Manufacturers Corporation: Executive Power to Protect Local Industries | 6193 |
| BA096 | Judicial Renaissance -- Ch. 22: The HRET at Work | 6765 |
| BA100 | Liberty and Prosperity -- Ch. 21: David v. Arroyo: Constitutionality of Proclaiming a State of National Emergency | 6420 |

## Flags
**Rights**
- All rows use "CJP-authored, covered by the FLP corpus permission".
- **FLAG, Love God, Serve Man (22 rows):** published by the Philippine Daily Inquirer and edited by Isagani Yambot, whose editor's notes open every piece. Please confirm the PDI and editor consent, or strip the notes at B2.
- **FLAG, third-party text inside kept chapters:**
  - RtJ Ch. 1 (BD038): the APJR Executive Summary, an SC document.
  - LBE Ch. 5 (BD034): Davide's "Davide Watch" statement.
  - LBE Ch. 6 (BA059): House deliberations.
  - LBE Ch. 9 (BB015): statute and DOLE texts.
  - LBE Ch. 12 (BA063): a Comelec lawyer's report.

**Chapters not written by CJP.** None were registered. JR Ch. 4, LPF Ch. 9 and RtJ Ch. 2 and 10 were already skipped at B0.

**Dates**
- 20 rows use the chapter's own printed date (day precision): the LGSM pieces, L&P Ch. 16 and RtJ Ch. 13.
- The Chile lectures (LPF Ch. 10–14, March 2004) and JR Ch. 14 (Mining Summit, February 2005) use month precision.
- **FLAG, year-only dates (52 rows)**, because the file prints no month:
  - Leadership by Example (1999-01-01): the Preface is dated October 10, 1999.
  - Liberty and Prosperity (2006-01-01): current to July 31, 2006, printed about October 2006.
  - Five undated LGSM pieces (1994-01-01).
  - The team may prefer the Preface dates, at month precision.
- **FLAG:** RtJ Ch. 3 (AmCham) is dated to the book (2002-12). Its speech date, 2002-08-21, appears only in Salonga's skipped comment.

**Publisher.** Not stated in the file for Leadership by Example, Leveling the Playing Field and Liberty and Prosperity; recorded as "Not stated (probably Supreme Court Printing Services)".

**Source problems carried from B0**
- RtJ Ch. 22 (BA083) is truncated.
- Several books are missing their appendices and footnotes.
- Grouped pieces: LGSM Ch. 20 and 22, and L&P Ch. 8.

## Self-checks
| Check | Result |
|---|---|
| One manifest row per CHAPTER row (167 = 167); none for SKIP parts | **Pass** |
| No doc_id twice in the manifest, and none clashing with corpus/ or retired_doc_ids.csv | **Pass** |
| Every row has a theme, a YYYY-MM-DD date with a precision, and a rights status | **Pass** |
| Every source path exists | **Pass** |

**STOP.** Please confirm the IDs and themes, and any long-chapter splits, before B2.
