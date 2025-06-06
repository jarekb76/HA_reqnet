# Reqnet Recuperator - Instrukcja instalacji

## Wymagania wstępne

- Home Assistant z działającym brokerem MQTT
- Rekuperator Reqnet z modułem WiFi w wersji 0 lub nowszej
- Połączenie sieciowe między Home Assistant a rekuperatorem

## Krok 1: Konfiguracja dodatkowego brokera MQTT w rekuperatorze

Przed instalacją integracji należy skonfigurować rekuperator tak, aby łączył się z brokerem MQTT Home Assistant.

### Konfiguracja przez przeglądarkę internetową

1. **Znajdź IP rekuperatora w sieci lokalnej** (np. 192.168.7.1)

2. **Otwórz przeglądarkę** i wklej następujący adres, zastępując odpowiednie wartości:

```
http://IP_REKUPERATORA/API/RunFunction?name=ChangeAdditionalBrokerConfiguration&MQTT_ADDITIONAL_BROKER_ADDRESS=192.168.1.100&MQTT_ADDITIONAL_BROKER_PORT=1883&MQTT_ADDITIONAL_BROKER_USER=homeassistant&MQTT_ADDITIONAL_BROKER_PASSWORD=twoje_haslo_mqtt
```

**Przykład z rzeczywistymi wartościami:**
```
http://192.168.7.1/API/RunFunction?name=ChangeAdditionalBrokerConfiguration&MQTT_ADDITIONAL_BROKER_ADDRESS=192.168.1.100&MQTT_ADDITIONAL_BROKER_PORT=1883&MQTT_ADDITIONAL_BROKER_USER=homeassistant&MQTT_ADDITIONAL_BROKER_PASSWORD=mypassword123
```

**Zastąp:**
- `192.168.7.1` - rzeczywistym IP rekuperatora
- `192.168.1.100` - IP twojego Home Assistant z brokerem MQTT
- `homeassistant` - nazwą użytkownika MQTT w HA
- `mypassword123` - hasłem użytkownika MQTT

### Weryfikacja konfiguracji

Po wysłaniu komendy powinieneś otrzymać odpowiedź:
```json
{
  "ChangeAdditionalBrokerConfigurationResult": true,
  "Message": ""
}
```

Jeśli `ChangeAdditionalBrokerConfigurationResult` jest `true`, konfiguracja została zapisana pomyślnie.



## Krok 2: Instalacja integracji w Home Assistant

### Przez HACS (jeszcze nie dziala)

1. Otwórz HACS w Home Assistant
2. Przejdź do zakładki **Integrations**
3. Kliknij **Explore & Download Repositories**
4. Wyszukaj "Reqnet Recuperator"
5. Kliknij **Download**
6. Zrestartuj Home Assistant

### Instalacja ręczna

1. Pobierz najnowszą wersję z [GitHub](https://github.com/jarekb76/reqnet)
2. Skopiuj folder `custom_components/reqnet` do katalogu `custom_components` w Home Assistant
3. Zrestartuj Home Assistant

## Krok 3: Konfiguracja integracji

1. Przejdź do **Settings** → **Devices & Services**
2. Kliknij **Add Integration**
3. Wyszukaj "Reqnet Recuperator"
4. Podaj **IP Address** rekuperatora (np. 192.168.7.1)



## Przykład użycia serwisu

```yaml
# Ustawienie trybu ręcznego z nawiewem 300 i wyciągiem 280
service: reqnet.set_manual_mode
data:
  device_id: "ABCDEF123456"  # MAC bez dwukropków
  airflow_value: 300
  air_extraction_value: 280
```
# Wsparcie

Jeżeli podoba Ci się ten projekt, proszę kliknij gwiazdkę na [GitHub](https://github.com/jarekb76/reqnet) lub wesprzyj na [Sponsor](https://github.com/sponsors/jarekb76).

# Reqnet Recuperator - Installation Guide

## Prerequisites

- Home Assistant with working MQTT broker
- Reqnet recuperator with WiFi module version 0 or newer
- Network connection between Home Assistant and the recuperator

## Step 1: Configure additional MQTT broker in the recuperator

Before installing the integration, you need to configure the recuperator to connect to the Home Assistant MQTT broker.

### Configuration via web browser

1. **Find the recuperator's IP address in your local network** (e.g., 192.168.7.1)

2. **Open your web browser** and paste the following URL, replacing the appropriate values:

```
http://RECUPERATOR_IP/API/RunFunction?name=ChangeAdditionalBrokerConfiguration&MQTT_ADDITIONAL_BROKER_ADDRESS=192.168.1.100&MQTT_ADDITIONAL_BROKER_PORT=1883&MQTT_ADDITIONAL_BROKER_USER=homeassistant&MQTT_ADDITIONAL_BROKER_PASSWORD=your_mqtt_password
```

**Example with actual values:**
```
http://192.168.7.1/API/RunFunction?name=ChangeAdditionalBrokerConfiguration&MQTT_ADDITIONAL_BROKER_ADDRESS=192.168.1.100&MQTT_ADDITIONAL_BROKER_PORT=1883&MQTT_ADDITIONAL_BROKER_USER=homeassistant&MQTT_ADDITIONAL_BROKER_PASSWORD=mypassword123
```

**Replace:**
- `192.168.7.1` - with your recuperator's actual IP address
- `192.168.1.100` - with your Home Assistant's IP address with MQTT broker
- `homeassistant` - with your MQTT username in HA
- `mypassword123` - with your MQTT user password

### Configuration verification

After sending the command, you should receive a response:
```json
{
  "ChangeAdditionalBrokerConfigurationResult": true,
  "Message": ""
}
```

If `ChangeAdditionalBrokerConfigurationResult` is `true`, the configuration has been saved successfully.

## Step 2: Install the integration in Home Assistant

### Via HACS (not working yet)

1. Open HACS in Home Assistant
2. Go to the **Integrations** tab
3. Click **Explore & Download Repositories**
4. Search for "Reqnet Recuperator"
5. Click **Download**
6. Restart Home Assistant

### Manual installation

1. Download the latest version from [GitHub](https://github.com/jarekb76/reqnet)
2. Copy the `custom_components/reqnet` folder to the `custom_components` directory in Home Assistant
3. Restart Home Assistant

## Step 3: Configure the integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Reqnet Recuperator"
4. Enter the **IP Address** of the recuperator (e.g., 192.168.7.1)

## Service usage example

```yaml
# Set manual mode with airflow 300 and air extraction 280
service: reqnet.set_manual_mode
data:
  device_id: "ABCDEF123456"  # MAC address without colons
  airflow_value: 300
  air_extraction_value: 280
```

# Showing Your Appreciation

If you like this project, please give it a star on [GitHub](https://github.com/jarekb76/reqnet) or consider becoming a [Sponsor](https://github.com/sponsors/jarekb76).
