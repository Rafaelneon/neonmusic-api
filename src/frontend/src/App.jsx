import { useState, useEffect, useRef } from 'react'
import { Search, Play, Pause, Download, Music, Loader2, Volume2, SkipBack, SkipForward, Repeat, Shuffle } from 'lucide-react'
import { musicApi } from './api/music'

function App() {
  const [tracks, setTracks] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(null)
  const [currentTrack, setCurrentTrack] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const audioRef = useRef(null)

  useEffect(() => {
    fetchTracks()
  }, [])

  const fetchTracks = async () => {
    try {
      const data = await musicApi.getTracks()
      if (data.success) setTracks(data.tracks)
    } catch (err) {
      console.error("Erro ao buscar músicas:", err)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query) return
    
    setLoading(true)
    try {
      const res = await musicApi.downloadMusic(query)
      if (res.success) {
        if (res.status === 'ready') {
          fetchTracks()
        } else {
          pollStatus(res.task_id)
        }
      }
    } catch (err) {
      alert("Erro ao iniciar download: " + err.message)
    } finally {
      setLoading(false)
      setQuery('')
    }
  }

  const pollStatus = (taskId) => {
    setDownloading({ taskId, progress: 0 })
    const interval = setInterval(async () => {
      try {
        const res = await musicApi.getStatus(taskId)
        if (res.success) {
          const { status, progress } = res.task
          if (status === 'completed') {
            clearInterval(interval)
            setDownloading(null)
            fetchTracks()
          } else if (status === 'failed') {
            clearInterval(interval)
            setDownloading(null)
            alert("Falha no download: " + (res.task.error || "Erro desconhecido"))
          } else {
            setDownloading({ taskId, progress })
          }
        }
      } catch (err) {
        clearInterval(interval)
        setDownloading(null)
      }
    }, 2000)
  }

  const playTrack = (track) => {
    if (currentTrack?.id === track.id) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play()
      }
      setIsPlaying(!isPlaying)
    } else {
      setCurrentTrack(track)
      setIsPlaying(true)
      if (audioRef.current) {
        audioRef.current.src = track.stream_url
        audioRef.current.play()
      }
    }
  }

  const updateProgress = () => {
    if (audioRef.current) {
      const value = (audioRef.current.currentTime / audioRef.current.duration) * 100
      setProgress(value || 0)
    }
  }

  const handleProgressChange = (e) => {
    const newTime = (e.target.value / 100) * audioRef.current.duration
    audioRef.current.currentTime = newTime
    setProgress(e.target.value)
  }

  return (
    <div className="flex flex-col h-screen bg-[#000000] text-[#b3b3b3] font-sans overflow-hidden">
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 bg-black p-6 flex flex-col gap-8 hidden md:flex">
          <div className="text-white flex items-center gap-2 text-2xl font-bold mb-4">
            <div className="bg-light p-1 rounded-full text-black">
              <Music size={24} />
            </div>
            <span>MusicDown</span>
          </div>
          
          <nav className="flex flex-col gap-4 text-sm font-bold">
            <a href="#" className="flex items-center gap-4 text-white hover:text-white transition">
              <Music size={24} /> Início
            </a>
            <a href="#" className="flex items-center gap-4 hover:text-white transition">
              <Search size={24} /> Buscar
            </a>
            <div className="mt-4 pt-4 border-t border-gray-800">
              <p className="text-[11px] uppercase tracking-widest text-gray-500 mb-4">Sua Biblioteca</p>
              <div className="flex items-center gap-4 hover:text-white transition cursor-pointer">
                <div className="w-12 h-12 bg-gradient-to-br from-indigo-700 to-blue-300 rounded flex items-center justify-center text-white">
                  <Play size={20} fill="currentColor" />
                </div>
                <span>Músicas Curtidas</span>
              </div>
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto bg-gradient-to-b from-[#1e1e1e] to-[#121212] relative">
          {/* Header/Top Bar */}
          <header className="sticky top-0 z-10 p-4 flex justify-between items-center bg-[#121212]/80 backdrop-blur-md">
            <div className="flex gap-4">
               <button className="w-8 h-8 bg-black/40 rounded-full flex items-center justify-center text-white cursor-not-allowed">
                 <SkipBack size={18} />
               </button>
               <button className="w-8 h-8 bg-black/40 rounded-full flex items-center justify-center text-white cursor-not-allowed">
                 <SkipForward size={18} />
               </button>
            </div>
            
            <form onSubmit={handleSearch} className="relative w-full max-w-md">
              <input
                type="text"
                placeholder="O que você quer ouvir?"
                className="w-full bg-white text-black rounded-full py-2.5 px-12 text-sm focus:outline-none placeholder-gray-500"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <Search className="absolute left-4 top-2.5 w-5 h-5 text-gray-500" />
              {loading && <Loader2 className="absolute right-4 top-2.5 w-5 h-5 animate-spin text-light" />}
            </form>

            <div className="flex items-center gap-4">
               <button className="text-sm font-bold hover:scale-105 transition text-white">Inscrever-se</button>
               <button className="bg-white text-black px-8 py-2.5 rounded-full text-sm font-bold hover:scale-105 transition">Entrar</button>
            </div>
          </header>

          <div className="p-8">
            <h2 className="text-3xl font-bold text-white mb-6">Suas Músicas</h2>
            
            {downloading && (
              <div className="mb-8 p-6 bg-[#282828] rounded-lg shadow-2xl border border-light/20">
                <div className="flex justify-between items-center mb-3">
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-5 h-5 animate-spin text-light" />
                    <span className="text-white font-bold">Processando novo download...</span>
                  </div>
                  <span className="text-light font-mono font-bold">{downloading.progress}%</span>
                </div>
                <div className="w-full bg-[#3e3e3e] rounded-full h-1.5">
                  <div 
                    className="bg-light h-1.5 rounded-full transition-all duration-700 ease-out shadow-[0_0_10px_#1ed760]" 
                    style={{ width: `${downloading.progress}%` }}
                  ></div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-6">
              {tracks.map((track) => (
                <div 
                  key={track.id} 
                  className="bg-[#181818] p-4 rounded-lg hover:bg-[#282828] transition-all duration-300 group cursor-pointer shadow-lg relative"
                  onClick={() => playTrack(track)}
                >
                  <div className="relative mb-4 aspect-square overflow-hidden rounded-md shadow-[0_8px_24px_rgba(0,0,0,0.5)]">
                    <img 
                      src={track.thumbnail || 'https://via.placeholder.com/300?text=No+Cover'} 
                      alt={track.title}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                    <button className="absolute bottom-2 right-2 w-12 h-12 bg-light rounded-full flex items-center justify-center shadow-2xl opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300 text-black hover:scale-105 active:scale-95">
                      {currentTrack?.id === track.id && isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" className="ml-1" />}
                    </button>
                  </div>
                  <h3 className="text-white font-bold truncate mb-1 text-base" title={track.title}>{track.title}</h3>
                  <p className="text-sm font-medium text-[#a7a7a7]">
                    {Math.floor(track.duration / 60)}:{(track.duration % 60).toString().padStart(2, '0')} • MP3
                  </p>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>

      {/* Footer Player (Style Spotify) */}
      <footer className="h-[90px] bg-black border-t border-[#282828] px-4 flex items-center justify-between z-20">
        {/* Track Info */}
        <div className="flex items-center gap-4 w-[30%] min-w-[180px]">
          {currentTrack ? (
            <>
              <div className="relative w-14 h-14 rounded overflow-hidden shadow-lg flex-shrink-0">
                <img src={currentTrack.thumbnail} className="w-full h-full object-cover" alt="" />
              </div>
              <div className="overflow-hidden">
                <div className="text-white text-sm font-bold truncate hover:underline cursor-pointer">{currentTrack.title}</div>
                <div className="text-[11px] text-[#a7a7a7] hover:underline cursor-pointer">Desconhecido</div>
              </div>
            </>
          ) : (
            <div className="flex items-center gap-4 opacity-50">
              <div className="w-14 h-14 bg-[#282828] rounded"></div>
              <div className="flex flex-col gap-2">
                <div className="w-24 h-3 bg-[#282828] rounded"></div>
                <div className="w-16 h-2 bg-[#282828] rounded"></div>
              </div>
            </div>
          )}
        </div>

        {/* Player Controls */}
        <div className="flex flex-col items-center gap-2 max-w-[40%] w-full">
          <div className="flex items-center gap-6 text-[#b3b3b3]">
            <Shuffle size={18} className="hover:text-white cursor-pointer" />
            <SkipBack size={20} fill="currentColor" className="hover:text-white cursor-pointer" />
            <button 
              onClick={() => currentTrack && playTrack(currentTrack)} 
              className="w-8 h-8 bg-white text-black rounded-full flex items-center justify-center hover:scale-105 active:scale-95 transition"
            >
              {isPlaying ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" className="ml-0.5" />}
            </button>
            <SkipForward size={20} fill="currentColor" className="hover:text-white cursor-pointer" />
            <Repeat size={18} className="hover:text-white cursor-pointer" />
          </div>
          
          <div className="flex items-center gap-2 w-full max-w-[600px] group">
            <span className="text-[11px] min-w-[30px] text-right">
              {audioRef.current ? Math.floor(audioRef.current.currentTime / 60) + ":" + Math.floor(audioRef.current.currentTime % 60).toString().padStart(2, '0') : "0:00"}
            </span>
            <input 
              type="range" 
              className="flex-1 h-1 bg-[#4d4d4d] rounded-full appearance-none cursor-pointer accent-white group-hover:accent-light"
              value={progress}
              onChange={handleProgressChange}
            />
            <span className="text-[11px] min-w-[30px]">
              {currentTrack ? Math.floor(currentTrack.duration / 60) + ":" + (currentTrack.duration % 60).toString().padStart(2, '0') : "0:00"}
            </span>
          </div>
          <audio 
            ref={audioRef} 
            onTimeUpdate={updateProgress}
            onEnded={() => setIsPlaying(false)} 
            className="hidden" 
          />
        </div>

        {/* Volume & Extra */}
        <div className="flex items-center justify-end gap-4 w-[30%] text-[#a7a7a7]">
          {currentTrack && (
            <a 
              href={currentTrack.stream_url} 
              download={`${currentTrack.title}.mp3`}
              className="p-2 hover:text-white hover:scale-110 transition flex items-center gap-1 group"
              title="Baixar MP3"
            >
              <Download size={20} />
              <span className="text-[10px] font-bold opacity-0 group-hover:opacity-100 transition-opacity">MP3</span>
            </a>
          )}
          <div className="flex items-center gap-2 w-32 group">
            <Volume2 size={20} className="group-hover:text-white" />
            <div className="flex-1 h-1 bg-[#4d4d4d] rounded-full overflow-hidden">
               <div className="bg-white group-hover:bg-light h-full w-[70%]"></div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
