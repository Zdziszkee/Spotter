from src.util.street_extractor import extract_street

def load_streetnames(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]

KNOWN_STREETNAMES = load_streetnames("street_names_krakow")

def test_ul_dot_no_space():
    text = "Mieszkanie przy ul.Lubomirskiego 10"
    expected = "lubomirska"
    assert extract_street(text, KNOWN_STREETNAMES) == expected

def test_ul_dot_with_space():
    text = "Nowy dom na ul. Lubomirskiego"
    expected = "lubomirska"
    assert extract_street(text, KNOWN_STREETNAMES) == expected

def test_ulica():
    text = "Sprzedam mieszkanie przy ulicy Lubomirskiego"
    expected = "lubomirska"
    assert extract_street(text, KNOWN_STREETNAMES) == expected

def test_aleja():
    text = "Luksusowe apartamenty przy aleja Lubomirskiego"
    expected = "lubomirska"
    assert extract_street(text, KNOWN_STREETNAMES) == expected

def test_hardcoded_modification_ending_iego():
    # Example: "ul. Nowakiego" should be modified to "Nowaka" from the known street list.
    streetnames = ["Nowaka"]
    text = "Mieszkanie przy ul. Nowakiego"
    expected = "Nowaka"
    assert extract_street(text, streetnames) == expected

def test_hardcoded_modification_ending_iej():
    # Example: "ul. Kowalskiej" should be modified to "Kowalska" from the known street list.
    streetnames = ["Kowalska"]
    text = "Nieruchomość przy ul. Kowalskiej"
    expected = "Kowalska"
    assert extract_street(text, streetnames) == expected

def test_no_match():
    text = "Brak informacji o ulicach i alejach."
    expected = ""
    assert extract_street(text, KNOWN_STREETNAMES) == expected

def test_monte_cassino():
    # Test for Klimatyczne, 3 pokojowe mieszkanie 71 m2, okolice ul. Monte Cassino
    streetnames = KNOWN_STREETNAMES + ["Monte Cassino"]
    text = """Klimatyczne, 3 pokojowe mieszkanie 71 m2, okolice ul. Monte Cassino Mieszkanie 56 m2 zlokalizowane jest w samym centrum Krakowa, w dzielnicy Stare Miasto, przy ul. Lubomirskiego, naprzeciwko Uniwersytetu Ekonomicznego, 2 min pieszo od dworca PKP oraz Galerii Krakowskiej, 15 min pieszo do Rynku Głównego.
    The Flat 56m2 , located in the heart of Cracow in Old Town district, at Lubomirski street, opposite to University of Economics, 3 min walking to the train station and shopping center – Galeria Krakowska, 15 min walking to the main square. Close to park and wide range of public transport."""
    expected = "monte cassino"
    assert extract_street(text, streetnames) == expected

def test_debskiego_two_rooms():
    # Test for property in Swoszowice / Opatkowice with ul. Dębskiego and 2 pokoje
    streetnames = KNOWN_STREETNAMES + ["Dębska"]
    text = """Nowoczesne mieszkanie: Swoszowice / Opatkowice / ul. Dębskiego / 2 pokoje Oferujemy Państwu bardzo przytulne i słoneczne mieszkanie znajdujące się na ul. Macieja Dębskiego 21d w dzielnicy Swoszowice / Opatkowice.

    Usytuowane na 2 piętrze, kameralnego, niskiego budynku z 2014 roku.

    Na powierzchnię 40m2 składa się pokój dzienny z aneksem kuchennym, sypialnia, przedpokój oraz łazienka z WC. Do lokalu przynależą dwa balkony po przeciwległych stronach - umożliwia to łatwe przewietrzenie.

    Mieszkanie w pełni wyposażone i umeblowane: w kuchni piekarnik, pralka, zmywarka, wiele szaf i schowków.

    Ogrzewanie za pomocą nowoczesnego gazowego pieca dwufunkcyjnego. Niskie opłaty administracyjne.

    Możliwość parkowania na ogólnodostępnych miejscach dla mieszkańców na dziedzińcu - brama zamykana na pilota.

    Dogodna lokalizacja na obrzeżach miasta - szybki dojazd do węzła autostrady A4. Nieopodal stacja kolejki "Opatkowice SKA" skąd dojazd do centrum miasta w 15min.

    OPŁATY: 2600zł + czynsz 400zł/1 osoba, 450zł/ 2 osoby + prąd i gaz
    Kaucja 3500zł."""
    expected = "dębska"
    assert extract_street(text, streetnames) == expected
