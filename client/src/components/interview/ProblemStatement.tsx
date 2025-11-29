import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChevronDown, ChevronUp, Copy } from 'lucide-react';
import { useState } from 'react';

interface ProblemStatementProps {
  title: string;
  content: string;
  examples?: {
    input: string;
    output: string;
    explanation?: string;
  }[];
  constraints?: string[];
  isVisible: boolean;
  className?: string;
}

export function ProblemStatement({
  title,
  content,
  examples = [],
  constraints = [],
  isVisible,
  className,
}: ProblemStatementProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (!isVisible) return null;

  const copyProblem = () => {
    const problemText = `
# ${title}

${content}

${
  examples.length > 0
    ? '## Examples\n\n' +
      examples
        .map(
          (ex, i) =>
            `Example ${i + 1}:\nInput: ${ex.input}\nOutput: ${ex.output}${ex.explanation ? '\nExplanation: ' + ex.explanation : ''}`
        )
        .join('\n\n')
    : ''
}

${constraints.length > 0 ? '## Constraints\n\n- ' + constraints.join('\n- ') : ''}
    `.trim();

    navigator.clipboard.writeText(problemText);
  };

  return (
    <div
      id="problem-statement"
      className={cn(
        'bg-slate-800 border border-slate-600 rounded-xl overflow-hidden transition-all',
        isCollapsed ? 'h-16' : 'h-[400px]',
        className
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-slate-600 bg-slate-700">
        <div className="flex items-center">
          <h3 className="font-medium text-lg text-slate-100">{title}</h3>
          <span className="ml-2 text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full border border-blue-500/30">
            Coding Challenge
          </span>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-slate-300 hover:text-slate-100 hover:bg-slate-600"
            onClick={copyProblem}
          >
            <Copy className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-slate-300 hover:text-slate-100 hover:bg-slate-600"
            onClick={() => setIsCollapsed(!isCollapsed)}
          >
            {isCollapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {!isCollapsed && (
        <ScrollArea className="h-[352px]">
          <div className="p-4 space-y-4">
            <div className="problem-description">
              <p className="text-slate-200 whitespace-pre-line">{content}</p>
            </div>

            {examples.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-semibold text-slate-100">Examples:</h4>
                {examples.map((example, index) => (
                  <div key={index} className="bg-slate-700 p-3 rounded-md border border-slate-600">
                    <p className="font-medium text-sm mb-1 text-slate-200">Example {index + 1}:</p>
                    <div className="space-y-1">
                      <p className="text-sm text-slate-300">
                        <span className="font-medium">Input:</span>{' '}
                        <code className="bg-slate-600 px-1 py-0.5 rounded text-blue-300">
                          {example.input}
                        </code>
                      </p>
                      <p className="text-sm text-slate-300">
                        <span className="font-medium">Output:</span>{' '}
                        <code className="bg-slate-600 px-1 py-0.5 rounded text-green-300">
                          {example.output}
                        </code>
                      </p>
                      {example.explanation && (
                        <p className="text-sm text-slate-300">
                          <span className="font-medium">Explanation:</span> {example.explanation}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {constraints.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-semibold text-slate-100">Constraints:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {constraints.map((constraint, index) => (
                    <li key={index} className="text-slate-300 text-sm">
                      {constraint}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
