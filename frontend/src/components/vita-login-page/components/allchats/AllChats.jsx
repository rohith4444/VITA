import React from "react";
import "./allchats.css";

const AllChats = ({ isRecentChats }) => {
    return (
        <>
            <div className="allchats">
                <div className="allchats_header">
                    <div className="allchats_heading">
                        <h2>{isRecentChats ? `Your recent chats` : `Your favorite chats`}</h2>
                    </div>
                    <div className="allchats_sort">

                    </div>
                </div>
                <div className="allchats_container">
                    {Array.from({ length: 3 }).map((_, index) => (
                    <div className="chat_card card" key={index}>
                        <h3 className="chat_card_heading">Project Structure for AI Agents and Tools</h3>
                        <p className="chat_card_time">4 hours ago</p>
                    </div>
                    ))}
                </div>
            </div>
        </>
    );
}

export default AllChats;