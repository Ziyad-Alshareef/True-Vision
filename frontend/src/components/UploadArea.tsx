import React, { useRef } from 'react';

interface UploadAreaProps {
  onUpload: (file: File) => void;
}

const UploadArea: React.FC<UploadAreaProps> = ({ onUpload }) => {
  const [isDragging, setIsDragging] = React.useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) onUpload(file);
  };

  const handleClick = (): void => {
    fileInputRef.current?.click();
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center ${
        isDragging ? 'border-green-500 bg-green-500/10' : 'border-gray-600'
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <p className="text-gray-300 mb-4">Drag and drop your video here, or click to upload</p>
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept="video/*"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onUpload(file);
        }}
      />
      <button className="bg-green-600 px-4 py-2 rounded-md hover:bg-green-700">
        Upload Video
      </button>
    </div>
  );
};

export default UploadArea; 