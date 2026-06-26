import { useState, useRef, useEffect } from "react";
import Icon from "@/components/ui/icon";

interface HistoryEntry {
  command: string;
  output: string;
  exit_code: number;
  timestamp: string;
}

const BACKEND_URL = "https://functions.poehali.dev/efb08ca2-8c87-48b4-aac8-6b30f85f37d2";

const Index = () => {
  const [command, setCommand] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [cmdHistory, setCmdHistory] = useState<string[]>([]);
  const [cmdHistoryIndex, setCmdHistoryIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const runCommand = async () => {
    const cmd = command.trim();
    if (!cmd || loading) return;

    setLoading(true);
    setCmdHistory((prev) => [cmd, ...prev]);
    setCmdHistoryIndex(-1);
    setCommand("");

    try {
      const res = await fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd }),
      });
      const data = await res.json();
      setHistory((prev) => [
        ...prev,
        {
          command: cmd,
          output: data.output || data.error || "(нет вывода)",
          exit_code: data.exit_code ?? -1,
          timestamp: new Date().toLocaleTimeString("ru-RU"),
        },
      ]);
    } catch {
      setHistory((prev) => [
        ...prev,
        {
          command: cmd,
          output: "Ошибка подключения к серверу",
          exit_code: -1,
          timestamp: new Date().toLocaleTimeString("ru-RU"),
        },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      runCommand();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const newIndex = Math.min(cmdHistoryIndex + 1, cmdHistory.length - 1);
      setCmdHistoryIndex(newIndex);
      setCommand(cmdHistory[newIndex] ?? "");
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      const newIndex = Math.max(cmdHistoryIndex - 1, -1);
      setCmdHistoryIndex(newIndex);
      setCommand(newIndex === -1 ? "" : cmdHistory[newIndex]);
    } else if (e.key === "l" && e.ctrlKey) {
      e.preventDefault();
      setHistory([]);
    }
  };

  return (
    <div
      className="min-h-screen bg-[#0d0d0d] text-[#e0e0e0] font-mono flex flex-col"
      onClick={() => inputRef.current?.focus()}
    >
      {/* Header */}
      <div className="border-b border-[#2a2a2a] px-6 py-3 flex items-center gap-3 bg-[#111111]">
        <div className="flex gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[#ff5f57]" />
          <span className="w-3 h-3 rounded-full bg-[#febc2e]" />
          <span className="w-3 h-3 rounded-full bg-[#28c840]" />
        </div>
        <span className="text-[#666] text-sm ml-2">Terminal — bash</span>
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={(e) => { e.stopPropagation(); setHistory([]); }}
            className="text-[#555] hover:text-[#aaa] transition-colors text-xs flex items-center gap-1"
            title="Очистить (Ctrl+L)"
          >
            <Icon name="Trash2" size={13} />
            очистить
          </button>
        </div>
      </div>

      {/* Output area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {history.length === 0 && !loading && (
          <div className="text-[#444] text-sm pt-2">
            <p>Добро пожаловать в веб-терминал.</p>
            <p className="mt-1">Введите команду и нажмите <span className="text-[#666]">Enter</span>.</p>
            <p className="mt-1 text-[#333]">↑↓ — история команд · Ctrl+L — очистить</p>
          </div>
        )}

        {history.map((entry, i) => (
          <div key={i} className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[#28c840] select-none">❯</span>
              <span className="text-[#c8c8c8]">{entry.command}</span>
              <span className="ml-auto text-[#333] text-xs">{entry.timestamp}</span>
            </div>
            <pre
              className={`whitespace-pre-wrap break-all text-sm leading-relaxed pl-5 ${
                entry.exit_code !== 0 ? "text-[#ff6b6b]" : "text-[#b0b0b0]"
              }`}
            >
              {entry.output}
            </pre>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-[#555] text-sm">
            <span className="text-[#28c840]">❯</span>
            <span>{command || cmdHistory[0]}</span>
            <span className="ml-1 animate-pulse">▋</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[#1e1e1e] bg-[#111111] px-6 py-3 flex items-center gap-3">
        <span className="text-[#28c840] text-sm select-none">❯</span>
        <input
          ref={inputRef}
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          placeholder="введите команду..."
          className="flex-1 bg-transparent outline-none text-[#e0e0e0] placeholder-[#333] text-sm caret-[#28c840]"
          spellCheck={false}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
        />
        <button
          onClick={(e) => { e.stopPropagation(); runCommand(); }}
          disabled={loading || !command.trim()}
          className="text-[#333] hover:text-[#28c840] disabled:opacity-20 transition-colors"
        >
          <Icon name="CornerDownLeft" size={16} />
        </button>
      </div>
    </div>
  );
};

export default Index;