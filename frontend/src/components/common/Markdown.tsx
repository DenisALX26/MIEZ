import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

type MarkdownProps = {
  children: string
  className?: string
  /**
   * "chat" tightens vertical spacing for assistant bubbles;
   * "doc" is the default longer-form layout used by reports.
   */
  variant?: 'chat' | 'doc'
}

const baseComponents: Components = {
  h1: ({ children }) => (
    <h1 className="text-base font-semibold tracking-tight mt-3 mb-1.5 first:mt-0">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-[0.95rem] font-semibold tracking-tight mt-3 mb-1.5 first:mt-0">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-sm font-semibold tracking-tight mt-2.5 mb-1 first:mt-0">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="text-sm font-semibold mt-2 mb-1 first:mt-0">{children}</h4>
  ),
  p: ({ children }) => <p className="leading-relaxed">{children}</p>,
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      className="text-[var(--primary)] hover:opacity-80 underline underline-offset-2 decoration-[var(--primary)]/40"
    >
      {children}
    </a>
  ),
  ul: ({ children }) => <ul className="list-disc pl-5 space-y-1 marker:text-[var(--muted-foreground)]">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1 marker:text-[var(--muted-foreground)]">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-[var(--primary)] pl-3 italic text-[var(--muted-foreground)]">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="border-[var(--border)] my-3" />,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  code: ({ className, children, ...props }) => {
    const isBlock = /language-/.test(className ?? '')
    if (isBlock) {
      return (
        <code className={`${className ?? ''} block`} {...props}>
          {children}
        </code>
      )
    }
    return (
      <code className="bg-[var(--input-background)] border border-[var(--border)] rounded px-1 py-0.5 text-[0.85em] font-mono">
        {children}
      </code>
    )
  },
  pre: ({ children }) => (
    <pre className="bg-[var(--input-background)] border border-[var(--border)] rounded-lg p-3 overflow-x-auto text-[0.85em] font-mono leading-relaxed">
      {children}
    </pre>
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto rounded-lg border border-[var(--border)] my-2">
      <table className="min-w-full text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-[var(--input-background)]">{children}</thead>,
  th: ({ children }) => (
    <th className="text-left text-[11px] uppercase tracking-[0.14em] font-semibold text-[var(--muted-foreground)] px-3 py-2">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-3 py-2 border-t border-[var(--border)] align-top">{children}</td>
  ),
  tr: ({ children }) => <tr>{children}</tr>,
  img: ({ src, alt }) => (
    <img src={src} alt={alt ?? ''} className="rounded-lg border border-[var(--border)] max-w-full my-2" />
  ),
}

const Markdown = ({ children, className, variant = 'doc' }: MarkdownProps) => {
  const spacing = variant === 'chat' ? 'space-y-1.5' : 'space-y-2.5'
  const containerClass = `${spacing} text-sm text-[var(--foreground)] break-words ${className ?? ''}`.trim()
  return (
    <div className={containerClass}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={baseComponents}>
        {children}
      </ReactMarkdown>
    </div>
  )
}

export default Markdown
