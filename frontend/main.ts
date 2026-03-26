import './style.css'

const chatWindow = document.getElementById('chat-window') as HTMLDivElement
const input = document.getElementById('user-input') as HTMLTextAreaElement
const sendBtn = document.getElementById('send-btn') as HTMLButtonElement

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const messages: Message[] = []
let threadId = crypto.randomUUID()

// Auto-resize textarea
input.addEventListener('input', () => {
  input.style.height = 'auto'
  input.style.height = Math.min(input.scrollHeight, 160) + 'px'
})
input.addEventListener('keydown', (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
})

// Suggestion pills
document.querySelectorAll<HTMLElement>('.suggestion').forEach(el => {
  el.addEventListener('click', () => {
    input.value = el.dataset.text ?? el.textContent ?? ''
    input.dispatchEvent(new Event('input'))
    input.focus()
  })
})

// ── DOM helpers ───────────────────────────────────────────────────────────────

function appendUserMessage(text: string) {
  const div = document.createElement('div')
  div.className = 'message user'
  div.textContent = text
  chatWindow.appendChild(div)
  scroll()
}

function createAssistantBubble(): HTMLSpanElement {
  const div = document.createElement('div')
  div.className = 'message assistant'
  const label = document.createElement('div')
  label.className = 'label'
  label.textContent = 'Assistant'
  const content = document.createElement('span')
  div.appendChild(label)
  div.appendChild(content)
  chatWindow.appendChild(div)
  scroll()
  return content
}

function showIndicator(text: string) {
  removeIndicator()
  const el = document.createElement('div')
  el.className = 'indicator'
  el.id = 'run-indicator'
  el.innerHTML = `<span class="dot"></span><span>${text}</span>`
  chatWindow.appendChild(el)
  scroll()
}

function removeIndicator() {
  document.getElementById('run-indicator')?.remove()
}

const toolPills: Record<string, HTMLElement> = {}

function showToolPill(toolCallId: string, toolName: string) {
  const el = document.createElement('div')
  el.className = 'tool-pill'
  el.id = `tool-${toolCallId}`
  el.innerHTML = `<span class="icon">⚙️</span><span>Calling <strong>${toolName}</strong>…</span>`
  chatWindow.appendChild(el)
  toolPills[toolCallId] = el
  scroll()
}

function removeToolPill(toolCallId: string) {
  toolPills[toolCallId]?.remove()
  delete toolPills[toolCallId]
}

function renderCharts(text: string) {
  const regex = /CHART::([a-f0-9-]{36})/g
  const seen = new Set<string>()
  let match: RegExpExecArray | null
  while ((match = regex.exec(text)) !== null) {
    const chartId = match[1]
    if (seen.has(chartId)) { continue }
    seen.add(chartId)
    const wrap = document.createElement('div')
    wrap.className = 'chart-wrap'
    const iframe = document.createElement('iframe')
    iframe.src = `/chart/${chartId}`
    iframe.title = 'Chart'
    wrap.appendChild(iframe)
    chatWindow.appendChild(wrap)
  }
  if (seen.size > 0) { scroll() }
}

function appendErrorBubble(msg: string) {
  const div = document.createElement('div')
  div.className = 'message assistant'
  div.style.borderColor = '#f38ba8'
  div.style.color = '#f38ba8'
  div.innerHTML = `<div class="label" style="color:#f38ba8">Error</div>${msg}`
  chatWindow.appendChild(div)
  scroll()
}

function scroll() {
  chatWindow.scrollTop = chatWindow.scrollHeight
}

// ── AG-UI SSE consumer ────────────────────────────────────────────────────────

async function sendMessage() {
  const text = input.value.trim()
  if (!text) { return }

  document.querySelectorAll('.chart-wrap').forEach(el => el.remove())

  appendUserMessage(text)
  messages.push({ id: crypto.randomUUID(), role: 'user', content: text })

  input.value = ''
  input.style.height = 'auto'
  sendBtn.disabled = true

  showIndicator('Thinking…')

  const body = {
    thread_id: threadId,
    run_id: crypto.randomUUID(),
    messages,
  }

  let assistantContent: HTMLSpanElement | null = null
  let fullText = ''

  try {
    const res = await fetch('/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      removeIndicator()
      appendErrorBubble(`HTTP ${res.status}: ${res.statusText}`)
      return
    }

    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) { break }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data:')) { continue }
        const raw = line.slice(5).trim()
        if (!raw) { continue }

        let evt: Record<string, string>
        try { evt = JSON.parse(raw) } catch { continue }

        switch (evt.type) {
          case 'TEXT_MESSAGE_START':
            removeIndicator()
            assistantContent = createAssistantBubble()
            fullText = ''
            break

          case 'TEXT_MESSAGE_CONTENT':
            if (assistantContent) {
              fullText += evt.delta
              assistantContent.textContent = fullText
              scroll()
            }
            break

          case 'TEXT_MESSAGE_END':
            renderCharts(fullText)
            messages.push({ id: evt.messageId ?? crypto.randomUUID(), role: 'assistant', content: fullText })
            assistantContent = null
            break

          case 'TOOL_CALL_START':
            showToolPill(evt.toolCallId, evt.toolCallName)
            break

          case 'TOOL_CALL_END':
            removeToolPill(evt.toolCallId)
            break

          case 'RUN_FINISHED':
            removeIndicator()
            break

          case 'RUN_ERROR':
            removeIndicator()
            appendErrorBubble(evt.message ?? 'Unknown error')
            break
        }
      }
    }
  } catch (err) {
    removeIndicator()
    appendErrorBubble(`Network error: ${(err as Error).message}`)
  } finally {
    sendBtn.disabled = false
    input.focus()
  }
}

sendBtn.addEventListener('click', sendMessage)
