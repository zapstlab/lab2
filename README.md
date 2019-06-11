# ĆWICZENIE: Obiekty i relacje w Cloudify

## Wstęp

Celem tego ćwiczenia jest zapoznanie się z tworzeniem bazowego blueprintu TOSCA dla Cloudify, w którym znajdziemy węzły (w rozumieniu TOSCA) oraz relacje między nimi. Pokażemy również w jaki sposób można powiązać skrypty konfiguracyjne (w tym przypadku napisane w języku Python) z tworzonymi węzłami oraz relacjami. W ćwiczeniu tym, wykorzystując CLI Cloudify, wykonamy proces obejmujący następujące kroki:

- wgrywanie Blueprintu do Cloudify
- utworzenie Deploymentu dla wgranego Blueprintu
- przeglądanie listy węzłów TOSCA wchodzących w skład utworzonego deploymentu
- urchomianie procesu instalacji przygotowanego wcześniej Deploymentu
- przeglądanie listy zdarzeń powstałych w wyniku wykonania 
- przeglądanie listy instancji węzłów TOSCA utworzonych w procesie instalacji deploymentu
- aktualizowanie utworzonego wcześniej deploymentu
- obserwacja zmian w instancjach węzłów i w zdarzeniach będących konsekwencją wykonanej aktualizacji Deploymentu

Niezależnie od CLI, w ćwiczeniu warto (i należy) korzystać również z pulpitu (Dashboard) Cloudify w celu graficznej weryfikacji przeprowadzanych operacji (operacje wykonywane w CLI można byłobyy również przeprowadzić z poziomu pulpitu). Sposób logowania się do dashboard Cloudify został opisany w ćwiczeniu 1.

UWAGA: Ćwiczenie obejmuje wybrane, bardzo podstawowe zagadnienia związane z tworzeniem szablonów TOSCA i tym samym niewielki wycinek udostępnianych przez Cloudify możliwości orkiestracyjnych. Oczywiście istnieje możliwość przeprowadzenia własnych prób dotyczących tworzenia szablonów i deploymentów na bazie pogłębionej analizy Cloudify. Takie nietrywialne i udokumentowane w sprawozdaniu próby będą honorowane uznaniowym bonusem punktowym w wysokości do 25% maksymalnej nominalnej oceny za ćwiczenie.

## TOSCA w naszym ćwiczeniu

Węzły i relacje TOSCA wykorzystywane w tym ćwiczeniu są powiązane ze skryptami konfiguracyjnymi Python. Jedynym zadaniem tych skryptów jest logowanie zmian cyklu poszczególnych składników Deploymentu (węzłów, relacji). Pozwala to jednak prześledzić ogólny sposób, w jaki skrypty takie są tworzone, zamieszczane w blueprincie i zarządzane przez Cloudify. Umożliwia zatem zapoznanie się z procesem wiązania węzłów TOSCA ze skryptami konfiguracyjnymi (tutaj na przykładzie Python, jednak w sposób dobrze oddający ogólną istotę zagadnienia). Ten ostatni aspekt jest szczególnie istotny w przypadku orkiestracji powiązanej z rekonfiguracją koponentów usługowych, gdy typową (czasem jedyną) metodą rekonfiguracji jest właśnie wykonywanie procedur skryptoweych dostarczanych np. przez dostawców komponentrów usługowych - muszą wówczas istnieć sposoby wiązania takich zewnętrznych skryptów "wykonawczych" (faktycznie rekonfigurujących komponenty) z abstrakcyjnymi operacjami poziomu specyfikacji TOSCA (wyznaczającymi "punkty" przeprowadzania rekonfiguracji w abstrakcyjnym scenariuszu orkiestracyjnym).

```
node_types:

  cloudify.nodes.vRouter:
    derived_from: cloudify.nodes.Router
    interfaces:
      cloudify.interfaces.lifecycle:
        start:
          implementation: scripts/router-start.py
          executor: central_deployment_agent
        stop:
          implementation: scripts/router-stop.py
          executor: central_deployment_agent

  cloudify.nodes.vLB:
    derived_from: cloudify.nodes.LoadBalancer
    interfaces:
      cloudify.interfaces.lifecycle:
        start:
          implementation: scripts/lb-start.py
          executor: central_deployment_agent
        stop:
          implementation: scripts/lb-stop.py
          executor: central_deployment_agent

  cloudify.nodes.vAS:
    derived_from: cloudify.nodes.ApplicationServer
    interfaces:
      cloudify.interfaces.lifecycle:
        start:
          implementation: scripts/as-start.py
          executor: central_deployment_agent
        stop:
          implementation: scripts/as-stop.py
          executor: central_deployment_agent
		  
  cloudify.nodes.vApplication:
    derived_from: cloudify.nodes.ApplicationModule
    interfaces:
      cloudify.interfaces.lifecycle:
        start:
          implementation: scripts/app-start.py
          executor: central_deployment_agent
        stop:
          implementation: scripts/app-stop.py
          executor: central_deployment_agent
		  
  cloudify.nodes.Net:
    derived_from: cloudify.nodes.Network
    interfaces:
      cloudify.interfaces.lifecycle:
        start:
          implementation: scripts/network-start.py
          executor: central_deployment_agent
        stop:
          implementation: scripts/network-stop.py
          executor: central_deployment_agent

relationships:

  cloudify.relationships.rtr_connected_to_network:
    derived_from: cloudify.relationships.connected_to
    source_interfaces:
      cloudify.interfaces.relationship_lifecycle:
        preconfigure:
          implementation: scripts/relationships/src-preconfigure.py
          executor: central_deployment_agent
        postconfigure:
          implementation: scripts/relationships/src-postconfigure.py
          executor: central_deployment_agent
        establish:
          implementation: scripts/relationships/src-establish.py
          executor: central_deployment_agent
        unlink:
          implementation: scripts/relationships/src-unlink.py
          executor: central_deployment_agent
    target_interfaces:
      cloudify.interfaces.relationship_lifecycle:
        preconfigure:
          implementation: scripts/relationships/trgt-preconfigure.py
          executor: central_deployment_agent
        postconfigure:
          implementation: scripts/relationships/trgt-postconfigure.py
          executor: central_deployment_agent
        establish:
          implementation: scripts/relationships/trgt-establish.py
          executor: central_deployment_agent
        unlink:
          implementation: scripts/relationships/trgt-unlink.py
          executor: central_deployment_agent

```
Typy węzłow TOSCA z pliku types.yaml umożliwiąją tworzenie prostych elementów sieciowych oraz umożliwiają modelowanie relacji między nimi. Dziedziczą one z bazowych węzłów dostępnych w Cloudify, a umożliwiających definiowanie złożonych węzłów w Blueprincie. W szczególności przygotowany zestaw węzłów udostępnia takie węzły, jak:

- Router
- Load Balancer
- Application Server
- Application Module
- Network

WSKAZÓWKA: Niezależnie od użycia edytorów tekstowych czy przeglądarki dla github, w dashboardzie Cloudify można dość wygodnie przeglądać całą źródłową strukturę i poszczególne pliki blueprintu zaimportowanego już do Cloudify. Podgląd ten jest dostępny w dolnej części zakładki "Local Blueprints" (widać ją w liście po lewej stronie głównego okna konsoli).

# Opis ćwiczenia

## KROK 1: Utwórz podstawową wersję topologii aplikacji
W tym kroku utworzymy podstawową topologię naszej aplikacji, która wygląda jak poniżej:

vRouter-1 <-> PublicNetwork

Zapoznaj się z Blueprintem, węzłami TOSCA dla deploymentu, węzłami TOSCA dla utworzonej instalacji oraz ze zdarzeniami wygenerowanymi podczas procesu instalacji. Zwróć uwagę w jakiej kolejności wykonywane są operacje zmiany cyklu życia węzłów oraz relacji między nimi. Sekwencja działąń ujęta jest poniżej (pamiętaj, że identyfikatory poniżej mogą wymagać dostosowania do Twojego projektu; w szczególnościi dotyczy to identyfikatora "realizacji"/execution w poleceniu cfy events list -e <exceution_id>).

```
cfy blueprint upload -b topology ./simple-topology.yaml
cfy deployment create topology-example -b topology
cfy nodes list
cfy executions start -d topology-example install
cfy node-instances list -d topology-example
cfy executions list -d topology-example
cfy events list -e e4627d9a-9ba9-4d1c-a415-2b14e8fc76bc 
```

Zwróć uwagę na to, czym się różni node od node-instance. W dashboardzie Cloudify zweryfikuj wykonane powyżej kroki, przejrzyj utworzony i zainstalowany deployment oraz zapoznaj się z logami instalacji.

## KROK 2: Utwórz rozszerzoną wersję topologii
W tym kroku utworzymy rozszerzoną topologię

vRouter-1 <-> PublicNetwork <-> vAPP-Server-1 [vAPP-1-1, vAPP-1-2]

Topologia ta będzie utworzona w Cloudify poprzez zmodyfikowanie poprzedniego Deploymentu na podstawie nowego Blueprintu. 
Na podstawie zdarzeń wykonania operacji aktualizacji deploymentu prześledź poszczególne kroki jego realizacji. Uruchomienie aktualizacji:

```
cfy deployments update topology-example -p ./extended-topology.yaml
```

Zweryfikuj ponownie listę węzłów oraz ich instancji. W jaki sposób deployment ten różni się od poprzedniego? - skomentuj krótko te różnice. Przesledź w zdarzeniach kolejność wykonywanych operacji na węzłach deploymentu podczas jego odinstalowania i ponownej instalacji (wykonaj tę sekwencję operacji/workflow-ów w ramach ćwiczenia).

## KROK 3: Utwórz docelową wersję topologii

W tym kroku utworzymy końcową wersję topologii. W tym celu samodzielnie przygotuj Blueprint o nazwie np. final-topology.yaml, który posłuży do utworzenia następującej topologii:

```
vRouter-1 <-> PublicNetwork <-> vLoadBalancer <-> InternalNetwork <-> vRouter-2 <-> ServiceNetwork: 
    <-> vAPP-Server-1 [vAPP-1-1, vAPP-1-2]
    <-> vAPP-Server-2 [vAPP-2-1, vAPP-2-2]
(dwukropek : na końcu linii oznacza, że elementy poprzedzone symbolem <-> w kolejnych liniach pozostają w 
bezpośredniej relacji TOSCA typu "connected_to" z ostatnim elementem linii z dwukropkiem - tutaj 
serwery 1, 2 są dołączone do ServiceNetwork)
```

Podpobnie jak poprzednio, utwórz tę docelową topologię aplikując utworzony przez Ciebie Blueprint do już istniejącego Deploymentu (uzyskanego w kroku 2). Zwróć uwagę na zmieniony sposób przekazania Blueprintu do polecenia update. Sprawdź eksperymentalnie dlaczego poprzedni sposób by nie zadziałał; w celu ustalenia przyczyn warto przejrzeć informacje dostępne w pulpicie (dashboard) Cloudify dostępnym przez przeglądarkę (dostęp do dashboard wg wytycznych z Ćwiczenia 1).
```
cfy blueprint upload -b topology-final ./final-topology.yaml
cfy deployments update topology-example -b topology-final
```
Sprawdź konfigurację uzyskanego w ten sposób Deploymentu pod kątem zgodności z wymaganiami. W przypadku różnic wprowadź niezbędne poprawki do Blueprintu i zmodyfikuj Deployment ponownie.

## Krok 4: Proste skalowanie serwera

Teraz zilustrujemy operację skalowania komponentu aplikacji na przykładzie serwera aplikacyjnego. W tym celu (1) zmodyfikuj Blueprint wprowadzając możliwość skalowania wybranego serwera aplikacyjnego (w Blueprincie mamy zdefiniowane dwa szablony serwerowe: vAPP-Server-1, 2 - do skalowanie wybieramy dowolny z nich), (2) zmodyfikuj deployment korzystając z nowego blueprintu, a następnie (3) z dashboardu Cloudify przeprowadź operacje skalowania w górę i skalowania w dół dla serwera aplikacyjnego przewidzialnego do skalowania. Podstawy skalowania w Cloudify są opisane pod tym linkiem: https://docs.cloudify.co/4.6/developer/blueprints/multiple-instances/. WSKAZÓWKA: skalując z poziomu dashboard Cloudify, w polach "exclude-instances" i "include-instances" należy wpisać symbol listy pustej [], gdyż pozostawienie tych pól całkowicie niewypełnionych (skądinąd zgodne z intuicją) powoduje błąd wykonania sygnalizowany mało czytelnym komunikatem.

UWAGA: W Cloudify istnieje możliwość definiowania skryptów w języku Python realizujących własne workflow-y skalujące, jednak zadanie to wykracza poza ramy naszego ćwiczenia. Więcej na ten temat można znaleźć w dokumentacji Cloudify https://docs.cloudify.co/4.6/working_with/workflows/creating-your-own-workflow/.


# Sprawozdanie z ćwiczenia

Udokumentuj poszczególne kroki ćwiczenia zachowując odpowiednią numerację rozdziałów. W odrębnym punkcie podsumuj całe ćwiczenie.
