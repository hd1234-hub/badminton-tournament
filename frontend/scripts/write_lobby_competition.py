# -*- coding: utf-8 -*-
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src" / "pages" / "CreateLobbyCompetition.tsx"

S = {
    "err_count": "\u5f53\u524d\u8d5b\u5236\u62a5\u540d\u4eba\u6570\u9700\u4e3a",
    "err_set": "\u4f60\u8bbe\u7f6e\u4e86",
    "err_people": "\u4eba",
    "lobby_suffix": "\uff08\u5927\u5385\uff09",
    "fail": "\u521b\u5efa\u5931\u8d25",
    "back": "\u8fd4\u56de\u9996\u9875",
    "title": "\u521b\u5efa\u5927\u5385\u6bd4\u8d5b",
    "desc": "\u516c\u5f00\u62a5\u540d\uff0c\u4efb\u4f55\u4eba\u53ef\u5728\u6bd4\u8d5b\u5927\u5385\u52a0\u5165\uff0c\u65e0\u9700\u52a0\u5165\u4ff1\u4e50\u90e8\u3002",
    "name": "\u6bd4\u8d5b\u540d\u79f0",
    "name_ph": "\u4f8b\uff1a\u5468\u516b\u516b\u4eba\u8f6c",
    "format": "\u8d5b\u5236",
    "courts": "\u573a\u5730\u6570",
    "max": "\u62a5\u540d\u4eba\u6570\u4e0a\u9650",
    "deadline": "\u62a5\u540d\u622a\u6b62\u65f6\u95f4\uff08\u53ef\u9009\uff09",
    "creating": "\u521b\u5efa\u4e2d...",
    "publish": "\u53d1\u5e03\u5230\u5927\u5385",
}

CONTENT = f'''import {{ useState }} from "react";
import {{ Link, useNavigate }} from "react-router-dom";
import type {{ CompetitionFormat }} from "../types";
import {{ FORMAT_LABELS, FORMAT_PLAYER_COUNTS }} from "../types";
import * as compApi from "../api/competitions";

export default function CreateLobbyCompetition() {{
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [format, setFormat] = useState<CompetitionFormat>("eight_player_rotation");
  const [courts, setCourts] = useState(2);
  const [maxPlayers, setMaxPlayers] = useState("8");
  const [signupDeadline, setSignupDeadline] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const validCounts = FORMAT_PLAYER_COUNTS[format];
  const countLabel = validCounts.join("/");

  const handleSubmit = async (e: React.FormEvent) => {{
    e.preventDefault();
    setError("");
    const n = Number(maxPlayers);
    if (!validCounts.includes(n)) {{
      setError(`{S["err_count"]} ${{countLabel}}，{S["err_set"]} ${{n}} {S["err_people"]}`);
      return;
    }}
    setSubmitting(true);
    try {{
      const comp = await compApi.createCompetition({{
        name: name || `${{FORMAT_LABELS[format]}}{S["lobby_suffix"]}`,
        club_id: null,
        format,
        courts,
        player_ids: [],
        open_signup: true,
        is_public: true,
        max_players: n,
        signup_deadline: signupDeadline ? new Date(signupDeadline).toISOString() : undefined,
      }});
      navigate(`/competitions/${{comp.id}}`);
    }} catch (err: any) {{
      setError(err.response?.data?.detail || "{S["fail"]}");
    }} finally {{
      setSubmitting(false);
    }}
  }};

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link to="/" className="text-nailong-orange text-sm hover:text-nailong-orange-dark font-medium">&larr; {S["back"]}</Link>
      <h1 className="text-2xl font-bold text-gray-800">{S["title"]}</h1>
      <p className="text-gray-500 text-sm">{S["desc"]}</p>
      <form onSubmit={{handleSubmit}} className="card-nailong p-6 space-y-5">
        {{error && <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl text-sm">{{error}}</div>}}
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">{S["name"]}</label>
          <input value={{name}} onChange={{e => setName(e.target.value)}}
            placeholder="{S["name_ph"]}"
            className="input-nailong w-full" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">{S["format"]}</label>
          <select value={{format}} onChange={{e => setFormat(e.target.value as CompetitionFormat)}}
            className="input-nailong w-full">
            {{Object.entries(FORMAT_LABELS).map(([k, v]) => (
              <option key={{k}} value={{k}}>{{v}}</option>
            ))}}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">{S["courts"]}</label>
            <input type="number" min={{1}} max={{4}} value={{courts}}
              onChange={{e => setCourts(Number(e.target.value))}}
              className="input-nailong w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">{S["max"]} ({{countLabel}})</label>
            <input type="number" value={{maxPlayers}}
              onChange={{e => setMaxPlayers(e.target.value)}}
              className="input-nailong w-full" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">{S["deadline"]}</label>
          <input type="datetime-local" value={{signupDeadline}}
            onChange={{e => setSignupDeadline(e.target.value)}}
            className="input-nailong w-full" />
        </div>
        <button type="submit" disabled={{submitting}}
          className="btn-nailong w-full disabled:opacity-50">
          {{submitting ? "{S["creating"]}" : "{S["publish"]}"}}
        </button>
      </form>
    </div>
  );
}}
'''

OUT.write_text(CONTENT, encoding="utf-8")
print(f"Wrote {OUT}")
