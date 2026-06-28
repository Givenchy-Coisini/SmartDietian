import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import en from './en'

export type AppLocale = 'zh-CN' | 'en'

export const SUPPORTED_LOCALES: AppLocale[] = ['zh-CN', 'en']
export const LOCALE_STORAGE_KEY = 'app.lang'

function detectInitialLocale(): AppLocale {
  try {
    const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
    if (saved && (SUPPORTED_LOCALES as string[]).includes(saved)) {
      return saved as AppLocale
    }
  } catch {
    // localStorage 不可用（如隐私模式）时静默降级
  }
  return 'zh-CN'
}

const i18n = createI18n({
  legacy: false,
  locale: detectInitialLocale(),
  fallbackLocale: 'en',
  messages: {
    'zh-CN': zhCN,
    en
  }
})

export default i18n
