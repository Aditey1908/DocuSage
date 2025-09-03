

export function BackgroundGradientAnimation({
  children,
  className = "",
  containerClassName = "",
  animate = true
}) {
  return (
    <div className={`relative h-full w-full overflow-hidden ${containerClassName}`}>
      <div className={`absolute inset-0 z-0 ${className}`} 
           style={{ 
             background: 'linear-gradient(to right, #061b22, #1a2e35)',
           }}>
        <div
          className={`absolute -left-[20%] top-[10%] h-[60%] w-[60%] rounded-full bg-purple-600/60 mix-blend-screen blur-3xl 
                     ${animate ? 'animate-first' : ''}`}
        />
        <div
          className={`absolute -right-[20%] top-[20%] h-[70%] w-[70%] rounded-full bg-blue-500/70 mix-blend-screen blur-3xl 
                     ${animate ? 'animate-second' : ''}`}
        />
        <div
          className={`absolute bottom-[10%] left-[10%] h-[60%] w-[60%] rounded-full bg-cyan-400/70 mix-blend-screen blur-3xl 
                     ${animate ? 'animate-third' : ''}`}
        />
        <div
          className={`absolute -bottom-[40%] right-[10%] h-[80%] w-[80%] rounded-full bg-indigo-600/60 mix-blend-screen blur-3xl 
                     ${animate ? 'animate-fourth' : ''}`}
        />
        <div 
          className={`absolute -top-[10%] right-[30%] h-[50%] w-[50%] rounded-full bg-blue-700/70 mix-blend-screen blur-3xl 
                     ${animate ? 'animate-fifth' : ''}`}
        />
        <div className="absolute inset-0 backdrop-blur-[80px]" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent" />
      </div>
      <div className="relative z-10 h-full w-full">
        {children}
      </div>
    </div>
  );
}
