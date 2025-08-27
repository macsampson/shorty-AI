import React from "react"

interface HeaderProps {
  title?: string
}

const Header: React.FC<HeaderProps> = ({ title = "Shorty AI" }) => {
  return (
    <header className="flex justify-center items-center mb-8 py-4 px-6 rounded-lg bg-gradient-to-r from-primary to-purple-600 text-white shadow-md">
      <h1 className="text-2xl md:text-3xl font-bold tracking-tight m-0">
        {title}
      </h1>
    </header>
  )
}

export default Header
