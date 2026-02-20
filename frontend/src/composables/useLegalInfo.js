/**
 * Legal Info Composable
 *
 * Fetches company/legal information from the backend API.
 * Used by Impressum and Datenschutz pages.
 */

import { ref, onMounted } from 'vue'
import api from '../api/client.js'

const FALLBACK_LEGAL = {
  company_name: 'obo - Filip Ores',
  company_address: 'Nöltingstraße 31',
  company_postal_code: '22765',
  company_city: 'Hamburg',
  company_email: 'kontakt@obojobs.de',
  company_phone: ''
}

export function useLegalInfo() {
  const legal = ref({ ...FALLBACK_LEGAL })

  onMounted(async () => {
    try {
      const { data } = await api.get('/legal/info')
      legal.value = data
    } catch {
      legal.value = { ...FALLBACK_LEGAL }
    }
  })

  return { legal }
}

export default useLegalInfo
