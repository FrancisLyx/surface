import { useEffect, useId, useRef } from 'react'
import Cherry from 'cherry-markdown/dist/cherry-markdown.stream.esm'
import 'cherry-markdown/dist/cherry-markdown.min.css'

type CherryInstance = {
  setValue: (content: string) => void
  destroy: () => void
}

function CherryMarkdownViewer(props: { value: string }) {
  const containerId = useId().replace(/:/g, '-')
  const cherryRef = useRef<CherryInstance | null>(null)

  useEffect(() => {
    cherryRef.current = new Cherry({
      id: containerId,
      value: props.value,
    }) as CherryInstance

    return () => {
      cherryRef.current?.destroy()
      cherryRef.current = null
    }
  }, [containerId, props.value])

  useEffect(() => {
    cherryRef.current?.setValue(props.value)
  }, [props.value])

  return <div id={containerId} className="cherry-markdown-viewer" />
}

export default CherryMarkdownViewer
