# ĆWICZENIE: Obiekty i relacje w Cloudify
Celem tego ćwiczenia jest zapoznanie się z tworzeniem bazowego blueprintu TOSCA dla Cloudify, w którym znajdziemy węzły (w rozumieniu TOSCA) oraz relacje między nimi. Ćwiczenie pokaże również w jaki sposób można powiązać skrypty konfiguracyjne (w tym przypadku napisane w języku Python) z tworzonymi węzłami oraz relacjami. W ćwiczeniu tym, wykorzystując CLI Cloudify, wykonamy proces obejmujący następujące kroki:
- wgrawanie Blueprintu do Cloudify
- utworzenie Deploymentu dla wgranego Blueprintu
- przeglądanie listy węzłów TOSCA wchodzących w skład utworzonego deploymentu
- urchomianie procesu instalacji przygotowanego wcześniej Deploymentu
- przeglądanie listy zdarzeń powstałych w wyniku wykonania 
- przeglądanie listy instancji węzłów TOSCA utworzonych w procesie instalacji deploymentu
- aktualizowanie utworzonego wcześniej deploymentu
- obserwacja zmian w instancjach węzłów i w zdarzeniach będących konsekwencją wykonanej aktualizacji Deploymentu

Węzły i relacje TOSCA wykorzystywane w tym ćwiczeniu są powiązane ze skryptami konfiguracyjnymi Python. Celem tych skryptów jest logowanie zmian cyklu poszczególnych składników Deploymentu (węzłów, relacji), co pozwala prześledzić sposób, w jaki są one tworzone i zarządzane przez Cloudify. Umożliwia to również zapoznanie się z procesem wiązania węzłów TOSCA ze skryptami konfiguracyjnymi (na przykładzie Python, jednak dobrze oddający ogólną istotę zagadnienia). Ten ostatni aspekt jest szczególnie istotny w przypadku orkiestracji powiązanej z rekonfiguracją koponentów usługowych, gdy typową (czasem jedyną) metodą rekonfiguracji jest właśnie wykonywanie procedur skryptoweych dostarczanych np. przez dostawców komponentrów usługowych - muszą wówczas istnieć sposoby wiązania takich zewnętrznych skryptów z abstrakcyjnymi operacjami poziomu specyfikacji TOSCA.

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
Typy węzłow TOSCA z pliku types.yaml umożliwiąją tworzenie prostych elementów sieciowych oraz umożliwiają modelowanie relacji między nimi. Dziedziczą one z bazowych węzłów dostepnych w Cloudify, a umożliwiających tworzenie złożonych węzłów zdefiniowanych w Blueprincie. W szczególności przygotowany zestaw węzłów udostepnia takie węzły jak
- Router
- Load Balancer
- Application Server
- Application Module
- Network

# Przykłady blueprintów TOSCA

### KROK 1: Utworz podstawową wersję topologii
W tym kroku utworzymy podstawową topologię

vRouter-1 <-> PublicNetwork

Zapoznaj się z Blueprintem, węzłami TOSCA dla deploymentu, węzłami TOSCA dla utworzonej instalacji oraz ze zdarzeniami wygenerowanymi podczas procesu instalacji. Zwróć uwagę w jakiej kolejności wykonywane są operacje zmiany cyklu życia węzłów oraz relacji między nimi.

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

### KROK 2: Utwórz rozszerzoną wersję topologii
W tym kroku utworzymy rozszerzoną topologię

vRouter-1 <-> PublicNetwork <-> vAPP-Server-1 [vAPP-1-1, vAPP-1-2]

Topologia ta będzie utworzona w Cloudify poprzez zmodyfikowanie poprzedniego Deploymentu na podstawie nowego Blueprintu. 
Na podstawie zdarzeń wykonania operacji aktualizacji deploymentu prześledź poszczególne kroki jego realizacji. Uruchomienie aktualizacji:

```
cfy deployments update topology-example -p ./extended-topology.yaml
```

Zweryfikuj ponownie listę węzłów oraz ich instancji. W jaki sposób deployment ten różni się od poprzedniego? - skomentuj krótko te różnice. Przesledź w zdarzeniach kolejność wykonywanych operacji na węzłach deploymentu podczas jego odinstalowania i ponownej instalacji (wykonaj tę sekwencję operacji/workflow-ów w ramach ćwiczenia).

### KROK 3: Utwórz docelową wersję topologii

W tym kroku utworzymy końcową wersję topologii. W tym celu samodzielnie przygotuj Blueprint o nazwie np. final-topology.yaml, który posłuży do utworzenia następującej topologii:

```
vRouter-1 <-> PublicNetwork <-> vLoadBalancer <-> InternalNetwork <-> vRouter-2 <-> ServiceNetwork: 
    <-> vAPP-Server-1 [vAPP-1-1, vAPP-1-2]
    <-> vAPP-Server-2 [vAPP-2-1, vAPP-2-2]
(dwukropek : na końcu linii oznacza, że elementy poprzedzone <-> w kolejnych liniach pozostają w 
bezpośredniej relacji TOSCA typu "connected_to" z ostatnim elementem linii z dwukropkiem - tutaj 
serwery 1, 2 są dołączone do ServiceNetwork)
```

Podpobnie jak poprzednio, utwórz tę docelową topologię aplikując nowy Blueprint do już istniejącego Deploymentu (uzyskanego w kroku 2). Zwróć uwagę na zmieniony sposób przekazania blueprintu do polecenia update. Sprawdź eksperymentalnie dlaczego poprzedni sposób by nie zadziałał; w celu ustalenia przyczyn warto przejrzeć informacje dostępne w pulpicie dashboard CLoudify dostępnym przez przeglądarke (dostęp do dashboard wg wytycznych z Ćwiczenia 1).
```
cfy blueprint upload -b topology-final ./final-topology.yaml
cfy deployments update topology-example -b topology-final
```
# Sprawozdanie z ćwiczenia

### TBC
