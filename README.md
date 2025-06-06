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
