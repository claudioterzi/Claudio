import { SpeedInsights } from '@vercel/speed-insights/react'
import { isRrremergenLocation, sanitizeSpeedInsightsEvent } from './speed-insights-privacy.js'

function beforeSend(event) {
  if (!isRrremergenLocation(window.location)) return null
  return sanitizeSpeedInsightsEvent(event, window.location.origin)
}

export default function RrremergenSpeedInsights() {
  if (!import.meta.env.PROD || typeof window === 'undefined' ||
      !isRrremergenLocation(window.location)) return null

  return <SpeedInsights beforeSend={beforeSend} route="/rrremergen" sampleRate={1} debug={false} />
}
