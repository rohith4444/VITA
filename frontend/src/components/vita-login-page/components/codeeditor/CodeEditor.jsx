import React, { useRef, useState } from "react";
import "./codeeditor.css";
import { Editor } from "@monaco-editor/react";

const CodeEditor = () => {
    const [code, setCode] = useState('');
    const editorRef = useRef("");

    const onMount = (editor) => {
        editorRef.current = editor;
        editor.focus();
    }

    return (
        <>
            <Editor 
                height="100%"
                // language="" // add this for specific language from state
                defaultLanguage="java"
                defaultValue="// some comment"
                value={code}
                onChange={(code) => setCode(code)}
                onMount={onMount}
                options={{
                    // lineNumbers: "off",
                    minimap: { enabled: false }
                }}
                // theme="vs-dark"
            />
        </>
    );
};

export default CodeEditor;