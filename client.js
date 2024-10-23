import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Disc, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

const AudioProcessor = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [controls, setControls] = useState([
    { id: 1, type: 'SLOW', value: 0, pitch: true },
    { id: 2, type: 'SLOW', value: 0, pitch: true },
    { id: 3, type: 'SPEED', value: 0, pitch: true },
    { id: 4, type: 'SPEED', value: 0, pitch: true }
  ]);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
    setError(null);
  };

  const handleWheelChange = (id, newValue) => {
    setControls(controls.map(control => 
      control.id === id ? { ...control, value: newValue } : control
    ));
  };

  const handlePitchToggle = (id) => {
    setControls(controls.map(control => 
      control.id === id ? { ...control, pitch: !control.pitch } : control
    ));
  };

  const generateInstructions = () => {
    return controls
      .filter(control => control.value > 0)
      .map(control => 
        `${control.type}:${control.value}:${control.pitch ? 'PITCH' : 'NOPITCH'};`
      )
      .join('');
  };

  const handleProcess = async () => {
    try {
      setProcessing(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', selectedFile);
      
      const instructions = generateInstructions();
      if (instructions) {
        formData.append('instructions', instructions);
      }

      const response = await fetch('http://localhost:3000/process-audio', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Processing failed');
      }

      // Get the processed file and download it
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `processed_${selectedFile.name}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle>Audio Speed Processor</CardTitle>
      </CardHeader>
      <CardContent>
        {/* File Selection */}
        <div className="mb-8">
          <Label htmlFor="audio-file" className="block mb-2">Select Audio File</Label>
          <input
            id="audio-file"
            type="file"
            accept="audio/*"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Control Wheels */}
        <div className="grid grid-cols-2 gap-6 mb-8">
          {controls.map((control) => (
            <div key={control.id} className="flex flex-col items-center p-4 border rounded-lg">
              <div className="text-lg font-medium mb-2">
                {control.type === 'SLOW' ? 'Slow Down' : 'Speed Up'} {control.id}
              </div>
              
              <div className="relative mb-4">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={control.value}
                  onChange={(e) => handleWheelChange(control.id, parseInt(e.target.value))}
                  className="w-32"
                />
                <div className="absolute -top-2 left-full ml-2">
                  {control.value}%
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id={`pitch-${control.id}`}
                  checked={control.pitch}
                  onCheckedChange={() => handlePitchToggle(control.id)}
                />
                <Label htmlFor={`pitch-${control.id}`}>Preserve Pitch</Label>
              </div>
            </div>
          ))}
        </div>

        {/* Process Button */}
        <Button 
          onClick={handleProcess}
          disabled={!selectedFile || processing}
          className="w-full"
        >
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Disc className="mr-2 h-4 w-4" />
              Process Audio
            </>
          )}
        </Button>

        {/* Instructions Preview */}
        <div className="mt-4 p-2 bg-gray-50 rounded-md">
          <Label className="block mb-1">Generated Instructions:</Label>
          <code className="text-sm">{generateInstructions() || 'No modifications selected'}</code>
        </div>
      </CardContent>
    </Card>
  );
};

export default AudioProcessor;