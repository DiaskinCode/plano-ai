import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as Localization from 'expo-localization';

import en from '../locales/en.json';
import ru from '../locales/ru.json';

const resources = {
  en: { translation: en },
  ru: { translation: ru },
};

const getDeviceLanguage = () => {
  try {
    const locale = Localization.locale || Localization.getLocales()[0]?.languageCode;
    return locale ? locale.split('-')[0] : 'en';
  } catch {
    return 'en';
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: getDeviceLanguage(),
    fallbackLng: 'en',
    compatibilityJSON: 'v3',
    interpolation: {
      escapeValue: false, // React already escapes values
    },
  });

export default i18n;
