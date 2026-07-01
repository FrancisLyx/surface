import ReactMarkdown from 'react-markdown'
import rehypeHighlight from 'rehype-highlight'
import remarkGfm from 'remark-gfm'
import 'highlight.js/styles/github.css'

type MarkdownViewerProps = {
  value: string
}

function MarkdownViewer({ value }: MarkdownViewerProps) {
  return (
    <div className="markdown-viewer">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
        {value || '暂无内容'}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownViewer
