import React, { useState } from 'react';
import { Bot, Sparkles, AlertTriangle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../ui/Card';
import { Button } from '../ui/Button';
import { SAMPLE_NOTES } from '../../data/sampleScenario';

interface AICopilotProps {
  onOptimize: (notes: string[]) => void;
  isLoading: boolean;
}

export function AICopilot({ onOptimize, isLoading }: AICopilotProps) {
  const [notesText, setNotesText] = useState(SAMPLE_NOTES.join('\n\n'));
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    // Split by double newline, filter empty
    const notes = notesText.split('\n\n')
      .map(n => n.trim())
      .filter(n => n.length > 0);
      
    if (notes.length === 0) {
      setError('Please provide at least one operator instruction.');
      return;
    }
    
    if (notes.length > 3) {
      setError('Maximum 3 instructions supported per request.');
      return;
    }
    
    onOptimize(notes);
  };

  return (
    <Card className="border-green-200 shadow-md">
      <CardHeader className="bg-green-50/50 border-green-100">
        <div className="flex items-center space-x-2">
          <Bot className="h-6 w-6 text-green-600" />
          <CardTitle className="text-green-900">AI Energy Copilot</CardTitle>
        </div>
        <p className="text-sm text-green-700 mt-1">Describe operational requirements in natural language.</p>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <textarea
              className="w-full h-40 p-4 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm font-mono resize-none"
              placeholder="e.g. Reduce solar usage from 11–13 and maintain at least 40 kWh battery reserve during evening hours."
              value={notesText}
              onChange={(e) => setNotesText(e.target.value)}
              disabled={isLoading}
              maxLength={25000}
            />
            
            <p className="text-xs text-slate-500 flex items-center">
              <Sparkles className="h-3 w-3 mr-1 text-green-500" />
              Powered by Groq • Guardrailed • Independently validated. Separate multiple notes with a blank line (max 3).
            </p>
            
            {error && (
              <div className="p-3 bg-red-50 text-red-700 text-sm rounded-md flex items-start">
                <AlertTriangle className="h-4 w-4 mr-2 flex-shrink-0 mt-0.5" />
                {error}
              </div>
            )}
          </div>
        </CardContent>
        <CardFooter className="bg-slate-50 justify-end">
          <Button type="submit" size="lg" isLoading={isLoading} className="bg-green-600 hover:bg-green-700 w-full sm:w-auto shadow-[0_0_15px_rgba(22,163,74,0.3)]">
            <Sparkles className="h-4 w-4 mr-2" />
            Optimize with AI
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
